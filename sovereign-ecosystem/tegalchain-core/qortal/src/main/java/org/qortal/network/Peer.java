package org.qortal.network;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketTimeoutException;
import java.net.StandardSocketOptions;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.SocketChannel;
import java.security.SecureRandom;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.qortal.data.network.PeerChainTipData;
import org.qortal.data.network.PeerData;
import org.qortal.network.message.ChallengeMessage;
import org.qortal.network.message.Message;
import org.qortal.network.message.PingMessage;
import org.qortal.network.message.Message.MessageException;
import org.qortal.network.message.Message.MessageType;
import org.qortal.settings.Settings;
import org.qortal.utils.ExecuteProduceConsume;
import org.qortal.utils.NTP;

import com.google.common.hash.HashCode;
import com.google.common.net.HostAndPort;
import com.google.common.net.InetAddresses;

// For managing one peer
public class Peer {

	private static final Logger LOGGER = LogManager.getLogger(Peer.class);

	/** Maximum time to allow <tt>connect()</tt> to remote peer to complete. (ms) */
	private static final int CONNECT_TIMEOUT = 2000; // ms

	/** Maximum time to wait for a message reply to arrive from peer. (ms) */
	private static final int RESPONSE_TIMEOUT = 2000; // ms

	/**
	 * Interval between PING messages to a peer. (ms)
	 * <p>
	 * Just under every 30s is usually ideal to keep NAT mappings refreshed.
	 */
	private static final int PING_INTERVAL = 20_000; // ms

	private volatile boolean isStopping = false;

	private SocketChannel socketChannel = null;
	private InetSocketAddress resolvedAddress = null;
	/** True if remote address is loopback/link-local/site-local, false otherwise. */
	private boolean isLocal;

	private final Object byteBufferLock = new Object();
	private ByteBuffer byteBuffer;

	private Map<Integer, BlockingQueue<Message>> replyQueues;
	private LinkedBlockingQueue<Message> pendingMessages;

	/** True if we created connection to peer, false if we accepted incoming connection from peer. */
	private final boolean isOutbound;

	private final Object handshakingLock = new Object();
	private Handshake handshakeStatus = Handshake.STARTED;
	private volatile boolean handshakeMessagePending = false;

	/** Timestamp of when socket was accepted, or connected. */
	private Long connectionTimestamp = null;

	/** Last PING message round-trip time (ms). */
	private Long lastPing = null;
	/** When last PING message was sent, or null if pings not started yet. */
	private Long lastPingSent;

	byte[] ourChallenge;

	// Peer info

	private final Object peerInfoLock = new Object();

	private String peersNodeId;
	private byte[] peersPublicKey;
	private byte[] peersChallenge;

	private PeerData peerData = null;

	/** Peer's value of connectionTimestamp. */
	private Long peersConnectionTimestamp = null;

	/** Version string as reported by peer. */
	private String peersVersionString = null;
	/** Numeric version of peer. */
	private Long peersVersion = null;

	/** Latest block info as reported by peer. */
	private PeerChainTipData peersChainTipData;

	// Constructors

	/** Construct unconnected, outbound Peer using socket address in peer data */
	public Peer(PeerData peerData) {
		this.isOutbound = true;
		this.peerData = peerData;
	}

	/** Construct Peer using existing, connected socket */
	public Peer(SocketChannel socketChannel, Selector channelSelector) throws IOException {
		this.isOutbound = false;
		this.socketChannel = socketChannel;
		sharedSetup(channelSelector);

		this.resolvedAddress = ((InetSocketAddress) socketChannel.socket().getRemoteSocketAddress());
		this.isLocal = isAddressLocal(this.resolvedAddress.getAddress());

		PeerAddress peerAddress = PeerAddress.fromSocket(socketChannel.socket());
		this.peerData = new PeerData(peerAddress);
	}

	// Getters / setters

	public boolean isStopping() {
		return this.isStopping;
	}

	public SocketChannel getSocketChannel() {
		return this.socketChannel;
	}

	public InetSocketAddress getResolvedAddress() {
		return this.resolvedAddress;
	}

	public boolean isLocal() {
		return this.isLocal;
	}

	public boolean isOutbound() {
		return this.isOutbound;
	}

	public Handshake getHandshakeStatus() {
		synchronized (this.handshakingLock) {
			return this.handshakeStatus;
		}
	}

	/*package*/ void setHandshakeStatus(Handshake handshakeStatus) {
		synchronized (this.handshakingLock) {
			this.handshakeStatus = handshakeStatus;
		}
	}

	/*package*/ void resetHandshakeMessagePending() {
		this.handshakeMessagePending = false;
	}

	public PeerData getPeerData() {
		synchronized (this.peerInfoLock) {
			return this.peerData;
		}
	}

	public Long getConnectionTimestamp() {
		synchronized (this.peerInfoLock) {
			return this.connectionTimestamp;
		}
	}

	public String getPeersVersionString() {
		synchronized (this.peerInfoLock) {
			return this.peersVersionString;
		}
	}

	public Long getPeersVersion() {
		synchronized (this.peerInfoLock) {
			return this.peersVersion;
		}
	}

	/*package*/ void setPeersVersion(String versionString, long version) {
		synchronized (this.peerInfoLock) {
			this.peersVersionString = versionString;
			this.peersVersion = version;
		}
	}

	public Long getPeersConnectionTimestamp() {
		synchronized (this.peerInfoLock) {
			return this.peersConnectionTimestamp;
		}
	}

	/*package*/ void setPeersConnectionTimestamp(Long peersConnectionTimestamp) {
		synchronized (this.peerInfoLock) {
			this.peersConnectionTimestamp = peersConnectionTimestamp;
		}
	}

	public Long getLastPing() {
		synchronized (this.peerInfoLock) {
			return this.lastPing;
		}
	}

	/*package*/ void setLastPing(long lastPing) {
		synchronized (this.peerInfoLock) {
			this.lastPing = lastPing;
		}
	}

	/*package*/ byte[] getOurChallenge() {
		return this.ourChallenge;
	}

	public String getPeersNodeId() {
		synchronized (this.peerInfoLock) {
			return this.peersNodeId;
		}
	}

	/*package*/ void setPeersNodeId(String peersNodeId) {
		synchronized (this.peerInfoLock) {
			this.peersNodeId = peersNodeId;
		}
	}

	public byte[] getPeersPublicKey() {
		synchronized (this.peerInfoLock) {
			return this.peersPublicKey;
		}
	}

	/*package*/ void setPeersPublicKey(byte[] peerPublicKey) {
		synchronized (this.peerInfoLock) {
			this.peersPublicKey = peerPublicKey;
		}
	}

	public byte[] getPeersChallenge() {
		synchronized (this.peerInfoLock) {
			return this.peersChallenge;
		}
	}

	/*package*/ void setPeersChallenge(byte[] peersChallenge) {
		synchronized (this.peerInfoLock) {
			this.peersChallenge = peersChallenge;
		}
	}

	public PeerChainTipData getChainTipData() {
		synchronized (this.peerInfoLock) {
			return this.peersChainTipData;
		}
	}

	public void setChainTipData(PeerChainTipData chainTipData) {
		synchronized (this.peerInfoLock) {
			this.peersChainTipData = chainTipData;
		}
	}

	/*package*/ void queueMessage(Message message) {
		if (!this.pendingMessages.offer(message))
			LOGGER.info(() -> String.format("No room to queue message from peer %s - discarding", this));
	}

	@Override
	public String toString() {
		// Easier, and nicer output, than peer.getRemoteSocketAddress()
		return this.peerData.getAddress().toString();
	}

	// Processing

	private void sharedSetup(Selector channelSelector) throws IOException {
		this.connectionTimestamp = NTP.getTime();
		this.socketChannel.setOption(StandardSocketOptions.TCP_NODELAY, true);
		this.socketChannel.configureBlocking(false);
		this.socketChannel.register(channelSelector, SelectionKey.OP_READ);
		this.byteBuffer = null; // Defer allocation to when we need it, to save memory. Sorry GC!
		this.replyQueues = Collections.synchronizedMap(new HashMap<Integer, BlockingQueue<Message>>());
		this.pendingMessages = new LinkedBlockingQueue<>();

		Random random = new SecureRandom();
		this.ourChallenge = new byte[ChallengeMessage.CHALLENGE_LENGTH];
		random.nextBytes(this.ourChallenge);
	}

	public SocketChannel connect(Selector channelSelector) {
		LOGGER.trace(() -> String.format("Connecting to peer %s", this));

		try {
			this.resolvedAddress = this.peerData.getAddress().toSocketAddress();
			this.isLocal = isAddressLocal(this.resolvedAddress.getAddress());

			this.socketChannel = SocketChannel.open();
			this.socketChannel.socket().connect(resolvedAddress, CONNECT_TIMEOUT);
		} catch (SocketTimeoutException e) {
			LOGGER.trace(String.format("Connection timed out to peer %s", this));
			return null;
		} catch (UnknownHostException e) {
			LOGGER.trace(String.format("Connection failed to unresolved peer %s", this));
			return null;
		} catch (IOException e) {
			LOGGER.trace(String.format("Connection failed to peer %s", this));
			return null;
		}

		try {
			LOGGER.debug(() -> String.format("Connected to peer %s", this));
			sharedSetup(channelSelector);
			return socketChannel;
		} catch (IOException e) {
			LOGGER.trace(String.format("Post-connection setup failed, peer %s", this));
			try {
				socketChannel.close();
			} catch (IOException ce) {
				// Failed to close?
			}
			return null;
		}
	}

	/**
	 * Attempt to buffer bytes from socketChannel.
	 * 
	 * @throws IOException
	 */
	/* package */ void readChannel() throws IOException {
		synchronized (this.byteBufferLock) {
			while(true) {
				if (!this.socketChannel.isOpen() || this.socketChannel.socket().isClosed())
					return;

				// Do we need to allocate byteBuffer?
				if (this.byteBuffer == null)
					this.byteBuffer = ByteBuffer.allocate(Network.getInstance().getMaxMessageSize());

				final int priorPosition = this.byteBuffer.position();
				final int bytesRead = this.socketChannel.read(this.byteBuffer);
				if (bytesRead == -1) {
					this.disconnect("EOF");
					return;
				}

				LOGGER.trace(() -> {
					if (bytesRead > 0) {
						byte[] leadingBytes = new byte[Math.min(bytesRead, 8)];
						this.byteBuffer.asReadOnlyBuffer().position(priorPosition).get(leadingBytes);
						String leadingHex = HashCode.fromBytes(leadingBytes).toString();

						return String.format("Received %d bytes, starting %s, into byteBuffer[%d] from peer %s",
								bytesRead,
								leadingHex,
								priorPosition,
								this);
					} else {
						return String.format("Received %d bytes into byteBuffer[%d] from peer %s", bytesRead, priorPosition, this);
					}
				});
				final boolean wasByteBufferFull = !this.byteBuffer.hasRemaining();

				while (true) {
					final Message message;

					// Can we build a message from buffer now?
					ByteBuffer readOnlyBuffer = this.byteBuffer.asReadOnlyBuffer().flip();
					try {
						message = Message.fromByteBuffer(readOnlyBuffer);
					} catch (MessageException e) {
						LOGGER.debug(String.format("%s, from peer %s", e.getMessage(), this));
						this.disconnect(e.getMessage());
						return;
					}

					if (message == null && bytesRead == 0 && !wasByteBufferFull) {
						// No complete message in buffer, no more bytes to read from socket even though there was room to read bytes

						/* DISABLED
						// If byteBuffer is empty then we can deallocate it, to save memory, albeit costing GC
						if (this.byteBuffer.remaining() == this.byteBuffer.capacity())
							this.byteBuffer = null;
						*/

						return;
					}

					if (message == null)
						// No complete message in buffer, but maybe more bytes to read from socket
						break;

					LOGGER.trace(() -> String.format("Received %s message with ID %d from peer %s", message.getType().name(), message.getId(), this));

					// Tidy up buffers:
					this.byteBuffer.flip();
					// Read-only, flipped buffer's position will be after end of message, so copy that
					this.byteBuffer.position(readOnlyBuffer.position());
					// Copy bytes after read message to front of buffer, adjusting position accordingly, reset limit to capacity
					this.byteBuffer.compact();

					BlockingQueue<Message> queue = this.replyQueues.get(message.getId());
					if (queue != null) {
						// Adding message to queue will unblock thread waiting for response
						this.replyQueues.get(message.getId()).add(message);
						// Consumed elsewhere
						continue;
					}

					// No thread waiting for message so we need to pass it up to network layer

					// Add message to pending queue
					if (!this.pendingMessages.offer(message)) {
						LOGGER.info(() -> String.format("No room to queue message from peer %s - discarding", this));
						return;
					}

					// Prematurely end any blocking channel select so that new messages can be processed.
					// This might cause this.socketChannel.read() above to return zero into bytesRead.
					Network.getInstance().wakeupChannelSelector();
				}
			}
		}
	}

	/* package */ ExecuteProduceConsume.Task getMessageTask() {
		/*
		 * If we are still handshaking and there is a message yet to be processed then
		 * don't produce another message task. This allows us to process handshake
		 * messages sequentially.
		 */
		if (this.handshakeMessagePending)
			return null;

		final Message nextMessage = this.pendingMessages.poll();

		if (nextMessage == null)
			return null;

		LOGGER.trace(() -> String.format("Produced %s message task from peer %s", nextMessage.getType().name(), this));

		if (this.handshakeStatus != Handshake.COMPLETED)
			this.handshakeMessagePending = true;

		// Return a task to process message in queue
		return () -> Network.getInstance().onMessage(this, nextMessage);
	}

	/**
	 * Attempt to send Message to peer.
	 * 
	 * @param message
	 * @return <code>true</code> if message successfully sent; <code>false</code> otherwise
	 */
	public boolean sendMessage(Message message) {
		if (!this.socketChannel.isOpen())
			return false;

		try {
			// Send message
			LOGGER.trace(() -> String.format("Sending %s message with ID %d to peer %s", message.getType().name(), message.getId(), this));

			ByteBuffer outputBuffer = ByteBuffer.wrap(message.toBytes());

			synchronized (this.socketChannel) {
				while (outputBuffer.hasRemaining()) {
					int bytesWritten = this.socketChannel.write(outputBuffer);

					LOGGER.trace(() -> String.format("Sent %d bytes of %s message with ID %d to peer %s",
							bytesWritten,
							message.getType().name(),
							message.getId(),
							this));

					if (bytesWritten == 0)
						// Underlying socket's internal buffer probably full,
						// so wait a short while for bytes to actually be transmitted over the wire

						/*
						 * NOSONAR squid:S2276 - we don't want to use this.socketChannel.wait()
						 * as this releases the lock held by synchronized() above
						 * and would allow another thread to send another message,
						 * potentially interleaving them on-the-wire, causing checksum failures
						 * and connection loss.
						 */
						Thread.sleep(1L); //NOSONAR squid:S2276
				}
			}
		} catch (MessageException e) {
			LOGGER.warn(String.format("Failed to send %s message with ID %d to peer %s: %s", message.getType().name(), message.getId(), this, e.getMessage()));
		} catch (IOException e) {
			// Send failure
			return false;
		} catch (InterruptedException e) {
			// Likely shutdown scenario - so exit
			return false;
		}

		// Sent OK
		return true;
	}

	/**
	 * Send message to peer and await response.
	 * <p>
	 * Message is assigned a random ID and sent. If a response with matching ID is received then it is returned to caller.
	 * <p>
	 * If no response with matching ID within timeout, or some other error/exception occurs, then return <code>null</code>.<br>
	 * (Assume peer will be rapidly disconnected after this).
	 * 
	 * @param message
	 * @return <code>Message</code> if valid response received; <code>null</code> if not or error/exception occurs
	 * @throws InterruptedException
	 */
	public Message getResponse(Message message) throws InterruptedException {
		BlockingQueue<Message> blockingQueue = new ArrayBlockingQueue<>(1);

		// Assign random ID to this message
		Random random = new Random();
		int id;
		do {
			id = random.nextInt(Integer.MAX_VALUE - 1) + 1;

			// Put queue into map (keyed by message ID) so we can poll for a response
			// If putIfAbsent() doesn't return null, then this ID is already taken
		} while (this.replyQueues.putIfAbsent(id, blockingQueue) != null);
		message.setId(id);

		// Try to send message
		if (!this.sendMessage(message)) {
			this.replyQueues.remove(id);
			return null;
		}

		try {
			return blockingQueue.poll(RESPONSE_TIMEOUT, TimeUnit.MILLISECONDS);
		} finally {
			this.replyQueues.remove(id);
		}
	}

	/* package */ void startPings() {
		// Replacing initial null value allows getPingTask() to start sending pings.
		LOGGER.trace(() -> String.format("Enabling pings for peer %s", this));
		this.lastPingSent = NTP.getTime();
	}

	/* package */ ExecuteProduceConsume.Task getPingTask(Long now) {
		// Pings not enabled yet?
		if (now == null || this.lastPingSent == null)
			return null;

		// Time to send another ping?
		if (now < this.lastPingSent + PING_INTERVAL)
			return null; // Not yet

		// Not strictly true, but prevents this peer from being immediately chosen again
		this.lastPingSent = now;

		return () -> {
			PingMessage pingMessage = new PingMessage();
			Message message = this.getResponse(pingMessage);

			if (message == null || message.getType() != MessageType.PING) {
				LOGGER.debug(() -> String.format("Didn't receive reply from %s for PING ID %d", this, pingMessage.getId()));
				this.disconnect("no ping received");
				return;
			}

			this.setLastPing(NTP.getTime() - now);
		};
	}

	public void disconnect(String reason) {
		if (!isStopping)
			LOGGER.debug(() -> String.format("Disconnecting peer %s: %s", this, reason));

		this.shutdown();

		Network.getInstance().onDisconnect(this);
	}

	public void shutdown() {
		if (!isStopping)
			LOGGER.debug(() -> String.format("Shutting down peer %s", this));

		isStopping = true;

		if (this.socketChannel.isOpen()) {
			try {
				this.socketChannel.shutdownOutput();
				this.socketChannel.close();
			} catch (IOException e) {
				LOGGER.debug(String.format("IOException while trying to close peer %s", this));
			}
		}
	}

	// Utility methods

	/** Returns true if ports and addresses (or hostnames) match */
	public static boolean addressEquals(InetSocketAddress knownAddress, InetSocketAddress peerAddress) {
		if (knownAddress.getPort() != peerAddress.getPort())
			return false;

		return knownAddress.getHostString().equalsIgnoreCase(peerAddress.getHostString());
	}

	public static InetSocketAddress parsePeerAddress(String peerAddress) throws IllegalArgumentException {
		HostAndPort hostAndPort = HostAndPort.fromString(peerAddress).requireBracketsForIPv6();

		// HostAndPort doesn't try to validate host so we do extra checking here
		InetAddress address = InetAddresses.forString(hostAndPort.getHost());

		return new InetSocketAddress(address, hostAndPort.getPortOrDefault(Settings.getInstance().getDefaultListenPort()));
	}

	/** Returns true if address is loopback/link-local/site-local, false otherwise. */
	public static boolean isAddressLocal(InetAddress address) {
		return address.isLoopbackAddress() || address.isLinkLocalAddress() || address.isSiteLocalAddress();
	}

}

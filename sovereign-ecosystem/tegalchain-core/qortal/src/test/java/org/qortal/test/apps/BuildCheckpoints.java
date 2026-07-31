package org.qortal.test.apps;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.TreeMap;

import org.bitcoinj.core.BlockChain;
import org.bitcoinj.core.CheckpointManager;
import org.bitcoinj.core.NetworkParameters;
import org.bitcoinj.core.PeerAddress;
import org.bitcoinj.core.PeerGroup;
import org.bitcoinj.core.StoredBlock;
import org.bitcoinj.params.RegTestParams;
import org.bitcoinj.store.BlockStore;
import org.bitcoinj.store.MemoryBlockStore;

public class BuildCheckpoints {

	private static final TreeMap<Integer, StoredBlock> checkpoints = new TreeMap<>();

	public static void main(String[] args) throws Exception {
		final NetworkParameters params = RegTestParams.get();

		final BlockStore store = new MemoryBlockStore(params);
		final BlockChain chain = new BlockChain(params, store);
		final PeerGroup peerGroup = new PeerGroup(params, chain);

		final InetAddress ipAddress = InetAddress.getLoopbackAddress();
		final PeerAddress peerAddress = new PeerAddress(params, ipAddress);
		peerGroup.addAddress(peerAddress);
		peerGroup.start();

		chain.addNewBestBlockListener((block) -> checkpoints.put(block.getHeight(), block));

		peerGroup.downloadBlockChain();
		peerGroup.stop();

		final File checkpointsFile = new File("regtest-checkpoints");
		saveAsText(checkpointsFile);
	}

	private static void saveAsText(File textFile) {
		try (PrintWriter writer = new PrintWriter(
				new OutputStreamWriter(new FileOutputStream(textFile), StandardCharsets.US_ASCII))) {
			writer.println("TXT CHECKPOINTS 1");
			writer.println("0"); // Number of signatures to read. Do this later.
			writer.println(checkpoints.size());

			ByteBuffer buffer = ByteBuffer.allocate(StoredBlock.COMPACT_SERIALIZED_SIZE);

			for (StoredBlock block : checkpoints.values()) {
				block.serializeCompact(buffer);
				writer.println(CheckpointManager.BASE64.encode(buffer.array()));
				buffer.position(0);
			}
		} catch (FileNotFoundException e) {
			return;
		}
	}

}

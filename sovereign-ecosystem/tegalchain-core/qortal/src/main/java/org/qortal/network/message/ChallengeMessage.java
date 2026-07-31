package org.qortal.network.message;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;

import org.qortal.transform.Transformer;

public class ChallengeMessage extends Message {

	public static final int CHALLENGE_LENGTH = 32;

	private final byte[] publicKey;
	private final byte[] challenge;

	private ChallengeMessage(int id, byte[] publicKey, byte[] challenge) {
		super(id, MessageType.CHALLENGE);

		this.publicKey = publicKey;
		this.challenge = challenge;
	}

	public ChallengeMessage(byte[] publicKey, byte[] challenge) {
		this(-1, publicKey, challenge);
	}

	public byte[] getPublicKey() {
		return this.publicKey;
	}

	public byte[] getChallenge() {
		return this.challenge;
	}

	public static Message fromByteBuffer(int id, ByteBuffer byteBuffer)  {
		byte[] publicKey = new byte[Transformer.PUBLIC_KEY_LENGTH];
		byteBuffer.get(publicKey);

		byte[] challenge = new byte[CHALLENGE_LENGTH];
		byteBuffer.get(challenge);

		return new ChallengeMessage(id, publicKey, challenge);
	}

	@Override
	protected byte[] toData() throws IOException {
		ByteArrayOutputStream bytes = new ByteArrayOutputStream();

		bytes.write(this.publicKey);

		bytes.write(this.challenge);

		return bytes.toByteArray();
	}

}

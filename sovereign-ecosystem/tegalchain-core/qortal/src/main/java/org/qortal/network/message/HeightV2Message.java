package org.qortal.network.message;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.nio.ByteBuffer;

import org.qortal.transform.Transformer;
import org.qortal.transform.block.BlockTransformer;

import com.google.common.primitives.Ints;
import com.google.common.primitives.Longs;

public class HeightV2Message extends Message {

	private int height;
	private byte[] signature;
	private long timestamp;
	private byte[] minterPublicKey;

	public HeightV2Message(int height, byte[] signature, long timestamp, byte[] minterPublicKey) {
		this(-1, height, signature, timestamp, minterPublicKey);
	}

	private HeightV2Message(int id, int height, byte[] signature, long timestamp, byte[] minterPublicKey) {
		super(id, MessageType.HEIGHT_V2);

		this.height = height;
		this.signature = signature;
		this.timestamp = timestamp;
		this.minterPublicKey = minterPublicKey;
	}

	public int getHeight() {
		return this.height;
	}

	public byte[] getSignature() {
		return this.signature;
	}

	public long getTimestamp() {
		return this.timestamp;
	}

	public byte[] getMinterPublicKey() {
		return this.minterPublicKey;
	}

	public static Message fromByteBuffer(int id, ByteBuffer bytes) throws UnsupportedEncodingException {
		int height = bytes.getInt();

		byte[] signature = new byte[BlockTransformer.BLOCK_SIGNATURE_LENGTH];
		bytes.get(signature);

		long timestamp = bytes.getLong();

		byte[] minterPublicKey = new byte[Transformer.PUBLIC_KEY_LENGTH];
		bytes.get(minterPublicKey);

		return new HeightV2Message(id, height, signature, timestamp, minterPublicKey);
	}

	@Override
	protected byte[] toData() {
		try {
			ByteArrayOutputStream bytes = new ByteArrayOutputStream();

			bytes.write(Ints.toByteArray(this.height));

			bytes.write(this.signature);

			bytes.write(Longs.toByteArray(this.timestamp));

			bytes.write(this.minterPublicKey);

			return bytes.toByteArray();
		} catch (IOException e) {
			return null;
		}
	}

}

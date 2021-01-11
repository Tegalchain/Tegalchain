package org.qortal.network.message;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;

import com.google.common.primitives.Ints;

public class ResponseMessage extends Message {

	public static final int DATA_LENGTH = 32;

	private final int nonce;
	private final byte[] data;

	private ResponseMessage(int id, int nonce, byte[] data) {
		super(id, MessageType.RESPONSE);

		this.nonce = nonce;
		this.data = data;
	}

	public ResponseMessage(int nonce, byte[] data) {
		this(-1, nonce, data);
	}

	public int getNonce() {
		return this.nonce;
	}

	public byte[] getData() {
		return this.data;
	}

	public static Message fromByteBuffer(int id, ByteBuffer byteBuffer) {
		int nonce = byteBuffer.getInt();

		byte[] data = new byte[DATA_LENGTH];
		byteBuffer.get(data);

		return new ResponseMessage(id, nonce, data);
	}

	@Override
	protected byte[] toData() throws IOException {
		ByteArrayOutputStream bytes = new ByteArrayOutputStream(4 + DATA_LENGTH);

		bytes.write(Ints.toByteArray(this.nonce));

		bytes.write(data);

		return bytes.toByteArray();
	}

}

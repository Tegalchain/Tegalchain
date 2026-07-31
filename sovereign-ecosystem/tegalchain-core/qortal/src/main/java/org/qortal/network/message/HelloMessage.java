package org.qortal.network.message;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;

import org.qortal.transform.TransformationException;
import org.qortal.utils.Serialization;

import com.google.common.primitives.Longs;

public class HelloMessage extends Message {

	private final long timestamp;
	private final String versionString;

	private HelloMessage(int id, long timestamp, String versionString) {
		super(id, MessageType.HELLO);

		this.timestamp = timestamp;
		this.versionString = versionString;
	}

	public HelloMessage(long timestamp, String versionString) {
		this(-1, timestamp, versionString);
	}

	public long getTimestamp() {
		return this.timestamp;
	}

	public String getVersionString() {
		return this.versionString;
	}

	public static Message fromByteBuffer(int id, ByteBuffer byteBuffer) throws TransformationException {
		long timestamp = byteBuffer.getLong();

		String versionString = Serialization.deserializeSizedString(byteBuffer, 255);

		return new HelloMessage(id, timestamp, versionString);
	}

	@Override
	protected byte[] toData() throws IOException {
		ByteArrayOutputStream bytes = new ByteArrayOutputStream();

		bytes.write(Longs.toByteArray(this.timestamp));

		Serialization.serializeSizedString(bytes, this.versionString);

		return bytes.toByteArray();
	}

}

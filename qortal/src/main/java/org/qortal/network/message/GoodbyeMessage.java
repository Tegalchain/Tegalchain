package org.qortal.network.message;

import static java.util.Arrays.stream;
import static java.util.stream.Collectors.toMap;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.Map;

import com.google.common.primitives.Ints;

public class GoodbyeMessage extends Message {

	public enum Reason {
		NO_HELLO(1),
		BAD_HELLO(2),
		BAD_HELLO_VERSION(3),
		BAD_HELLO_TIMESTAMP(4);

		public final int value;

		private static final Map<Integer, Reason> map = stream(Reason.values())
				.collect(toMap(reason -> reason.value, reason -> reason));

		private Reason(int value) {
			this.value = value;
		}

		public static Reason valueOf(int value) {
			return map.get(value);
		}
	}

	private final Reason reason;

	private GoodbyeMessage(int id, Reason reason) {
		super(id, MessageType.GOODBYE);

		this.reason = reason;
	}

	public GoodbyeMessage(Reason reason) {
		this(-1, reason);
	}

	public Reason getReason() {
		return this.reason;
	}

	public static Message fromByteBuffer(int id, ByteBuffer byteBuffer) {
		int reasonValue = byteBuffer.getInt();

		Reason reason = Reason.valueOf(reasonValue);
		if (reason == null)
			return null;

		return new GoodbyeMessage(id, reason);
	}

	@Override
	protected byte[] toData() throws IOException {
		return Ints.toByteArray(this.reason.value);
	}

}

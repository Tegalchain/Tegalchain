package org.qortal.transform.transaction;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;

import org.qortal.data.transaction.ATTransactionData;
import org.qortal.data.transaction.TransactionData;
import org.qortal.transform.TransformationException;
import org.qortal.utils.Serialization;

import com.google.common.primitives.Ints;
import com.google.common.primitives.Longs;

public class AtTransactionTransformer extends TransactionTransformer {

	protected static final TransactionLayout layout = null;

	// Property lengths
	public static TransactionData fromByteBuffer(ByteBuffer byteBuffer) throws TransformationException {
		throw new TransformationException("Serialized AT transactions should not exist!");
	}

	public static int getDataLength(TransactionData transactionData) throws TransformationException {
		throw new TransformationException("Serialized AT transactions should not exist!");
	}

	// Used for generating fake transaction signatures
	public static byte[] toBytes(TransactionData transactionData) throws TransformationException {
		try {
			ATTransactionData atTransactionData = (ATTransactionData) transactionData;

			ByteArrayOutputStream bytes = new ByteArrayOutputStream();

			bytes.write(Ints.toByteArray(atTransactionData.getType().value));
			bytes.write(Longs.toByteArray(atTransactionData.getTimestamp()));
			bytes.write(atTransactionData.getReference());

			Serialization.serializeAddress(bytes, atTransactionData.getATAddress());

			Serialization.serializeAddress(bytes, atTransactionData.getRecipient());

			byte[] message = atTransactionData.getMessage();

			if (message != null) {
				// MESSAGE-type
				bytes.write(Ints.toByteArray(message.length));
				bytes.write(message);
			} else {
				// PAYMENT-type
				bytes.write(Longs.toByteArray(atTransactionData.getAssetId()));
				bytes.write(Longs.toByteArray(atTransactionData.getAmount()));
			}

			bytes.write(Longs.toByteArray(atTransactionData.getFee()));

			if (atTransactionData.getSignature() != null)
				bytes.write(atTransactionData.getSignature());

			return bytes.toByteArray();
		} catch (IOException | ClassCastException e) {
			throw new TransformationException(e);
		}
	}

}

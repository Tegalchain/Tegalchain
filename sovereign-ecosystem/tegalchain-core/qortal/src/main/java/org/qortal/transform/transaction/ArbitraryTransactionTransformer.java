package org.qortal.transform.transaction;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.List;

import org.qortal.crypto.Crypto;
import org.qortal.data.PaymentData;
import org.qortal.data.transaction.ArbitraryTransactionData;
import org.qortal.data.transaction.BaseTransactionData;
import org.qortal.data.transaction.TransactionData;
import org.qortal.data.transaction.ArbitraryTransactionData.DataType;
import org.qortal.transaction.ArbitraryTransaction;
import org.qortal.transaction.Transaction;
import org.qortal.transaction.Transaction.TransactionType;
import org.qortal.transform.PaymentTransformer;
import org.qortal.transform.TransformationException;
import org.qortal.utils.Serialization;

import com.google.common.primitives.Ints;
import com.google.common.primitives.Longs;

public class ArbitraryTransactionTransformer extends TransactionTransformer {

	// Property lengths
	private static final int SERVICE_LENGTH = INT_LENGTH;
	private static final int DATA_TYPE_LENGTH = BYTE_LENGTH;
	private static final int DATA_SIZE_LENGTH = INT_LENGTH;
	private static final int NUMBER_PAYMENTS_LENGTH = INT_LENGTH;

	private static final int EXTRAS_LENGTH = SERVICE_LENGTH + DATA_TYPE_LENGTH + DATA_SIZE_LENGTH;

	protected static final TransactionLayout layout;

	static {
		layout = new TransactionLayout();
		layout.add("txType: " + TransactionType.ARBITRARY.valueString, TransformationType.INT);
		layout.add("timestamp", TransformationType.TIMESTAMP);
		layout.add("transaction's groupID", TransformationType.INT);
		layout.add("reference", TransformationType.SIGNATURE);
		layout.add("sender's public key", TransformationType.PUBLIC_KEY);
		layout.add("number of payments", TransformationType.INT);

		layout.add("* recipient", TransformationType.ADDRESS);
		layout.add("* asset ID of payment", TransformationType.LONG);
		layout.add("* payment amount", TransformationType.AMOUNT);

		layout.add("service ID", TransformationType.INT);
		layout.add("is data raw?", TransformationType.BOOLEAN);
		layout.add("data length", TransformationType.INT);
		layout.add("data", TransformationType.DATA);
		layout.add("fee", TransformationType.AMOUNT);
		layout.add("signature", TransformationType.SIGNATURE);
	}

	public static TransactionData fromByteBuffer(ByteBuffer byteBuffer) throws TransformationException {
		long timestamp = byteBuffer.getLong();

		int version = Transaction.getVersionByTimestamp(timestamp);

		int txGroupId = byteBuffer.getInt();

		byte[] reference = new byte[REFERENCE_LENGTH];
		byteBuffer.get(reference);

		byte[] senderPublicKey = Serialization.deserializePublicKey(byteBuffer);

		// Always return a list of payments, even if empty
		List<PaymentData> payments = new ArrayList<>();
		if (version != 1) {
			int paymentsCount = byteBuffer.getInt();

			for (int i = 0; i < paymentsCount; ++i)
				payments.add(PaymentTransformer.fromByteBuffer(byteBuffer));
		}

		int service = byteBuffer.getInt();

		// We might be receiving hash of data instead of actual raw data
		boolean isRaw = byteBuffer.get() != 0;

		DataType dataType = isRaw ? DataType.RAW_DATA : DataType.DATA_HASH;

		int dataSize = byteBuffer.getInt();
		// Don't allow invalid dataSize here to avoid run-time issues
		if (dataSize > ArbitraryTransaction.MAX_DATA_SIZE)
			throw new TransformationException("ArbitraryTransaction data size too large");

		byte[] data = new byte[dataSize];
		byteBuffer.get(data);

		long fee = byteBuffer.getLong();

		byte[] signature = new byte[SIGNATURE_LENGTH];
		byteBuffer.get(signature);

		BaseTransactionData baseTransactionData = new BaseTransactionData(timestamp, txGroupId, reference, senderPublicKey, fee, signature);

		return new ArbitraryTransactionData(baseTransactionData, version, service, data, dataType, payments);
	}

	public static int getDataLength(TransactionData transactionData) throws TransformationException {
		ArbitraryTransactionData arbitraryTransactionData = (ArbitraryTransactionData) transactionData;

		int length = getBaseLength(transactionData) + EXTRAS_LENGTH + arbitraryTransactionData.getData().length;

		// Optional payments
		length += NUMBER_PAYMENTS_LENGTH + arbitraryTransactionData.getPayments().size() * PaymentTransformer.getDataLength();

		return length;
	}

	public static byte[] toBytes(TransactionData transactionData) throws TransformationException {
		try {
			ArbitraryTransactionData arbitraryTransactionData = (ArbitraryTransactionData) transactionData;

			ByteArrayOutputStream bytes = new ByteArrayOutputStream();

			transformCommonBytes(transactionData, bytes);

			List<PaymentData> payments = arbitraryTransactionData.getPayments();
			bytes.write(Ints.toByteArray(payments.size()));

			for (PaymentData paymentData : payments)
				bytes.write(PaymentTransformer.toBytes(paymentData));

			bytes.write(Ints.toByteArray(arbitraryTransactionData.getService()));

			bytes.write((byte) (arbitraryTransactionData.getDataType() == DataType.RAW_DATA ? 1 : 0));

			bytes.write(Ints.toByteArray(arbitraryTransactionData.getData().length));
			bytes.write(arbitraryTransactionData.getData());

			bytes.write(Longs.toByteArray(arbitraryTransactionData.getFee()));

			if (arbitraryTransactionData.getSignature() != null)
				bytes.write(arbitraryTransactionData.getSignature());

			return bytes.toByteArray();
		} catch (IOException | ClassCastException e) {
			throw new TransformationException(e);
		}
	}

	/**
	 * Signature for ArbitraryTransactions always uses hash of data, not raw data itself.
	 * 
	 * @param transactionData
	 * @return byte[]
	 * @throws TransformationException
	 */
	protected static byte[] toBytesForSigningImpl(TransactionData transactionData) throws TransformationException {
		ArbitraryTransactionData arbitraryTransactionData = (ArbitraryTransactionData) transactionData;

		try {
			ByteArrayOutputStream bytes = new ByteArrayOutputStream();

			transformCommonBytes(arbitraryTransactionData, bytes);

			if (arbitraryTransactionData.getVersion() != 1) {
				List<PaymentData> payments = arbitraryTransactionData.getPayments();
				bytes.write(Ints.toByteArray(payments.size()));

				for (PaymentData paymentData : payments)
					bytes.write(PaymentTransformer.toBytes(paymentData));
			}

			bytes.write(Ints.toByteArray(arbitraryTransactionData.getService()));

			bytes.write(Ints.toByteArray(arbitraryTransactionData.getData().length));

			// Signature uses hash of data, not raw data itself
			switch (arbitraryTransactionData.getDataType()) {
				case DATA_HASH:
					bytes.write(arbitraryTransactionData.getData());
					break;

				case RAW_DATA:
					bytes.write(Crypto.digest(arbitraryTransactionData.getData()));
					break;
			}

			bytes.write(Longs.toByteArray(arbitraryTransactionData.getFee()));

			// Never append signature

			return bytes.toByteArray();
		} catch (IOException | ClassCastException e) {
			throw new TransformationException(e);
		}
	}

}

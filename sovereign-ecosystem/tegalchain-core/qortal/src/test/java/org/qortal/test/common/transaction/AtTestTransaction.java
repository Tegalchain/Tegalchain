package org.qortal.test.common.transaction;

import org.qortal.account.PrivateKeyAccount;
import org.qortal.asset.Asset;
import org.qortal.crypto.Crypto;
import org.qortal.data.transaction.ATTransactionData;
import org.qortal.data.transaction.TransactionData;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;
import org.qortal.utils.Amounts;

public class AtTestTransaction extends TestTransaction {

	public static TransactionData randomTransaction(Repository repository, PrivateKeyAccount account, boolean wantValid) throws DataException {
		byte[] signature = new byte[64];
		random.nextBytes(signature);
		String atAddress = Crypto.toATAddress(signature);
		String recipient = account.getAddress();
		long amount = 123L * Amounts.MULTIPLIER;
		final long assetId = Asset.QORT;
		byte[] message = new byte[32];
		random.nextBytes(message);

		return new ATTransactionData(generateBase(account), atAddress, recipient, amount, assetId, message);
	}

}

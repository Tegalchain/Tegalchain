package org.qortal.test.common.transaction;

import org.qortal.account.PrivateKeyAccount;
import org.qortal.data.transaction.RewardShareTransactionData;
import org.qortal.data.transaction.TransactionData;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;

public class RewardShareTestTransaction extends TestTransaction {

	public static TransactionData randomTransaction(Repository repository, PrivateKeyAccount account, boolean wantValid) throws DataException {
		String recipient = account.getAddress();
		byte[] rewardSharePublicKey = account.getRewardSharePrivateKey(account.getPublicKey());
		int sharePercent = 50_00;

		return new RewardShareTransactionData(generateBase(account), recipient, rewardSharePublicKey, sharePercent);
	}

}

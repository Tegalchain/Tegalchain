package org.qortal.test.common.transaction;

import org.qortal.account.PrivateKeyAccount;
import org.qortal.data.transaction.AccountFlagsTransactionData;
import org.qortal.data.transaction.TransactionData;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;

public class AccountFlagsTestTransaction extends TestTransaction {

	public static TransactionData randomTransaction(Repository repository, PrivateKeyAccount account, boolean wantValid) throws DataException {
		final int andMask = -1;
		final int orMask = 0;
		final int xorMask = 0;

		return new AccountFlagsTransactionData(generateBase(account), account.getAddress(), andMask, orMask, xorMask);
	}

}

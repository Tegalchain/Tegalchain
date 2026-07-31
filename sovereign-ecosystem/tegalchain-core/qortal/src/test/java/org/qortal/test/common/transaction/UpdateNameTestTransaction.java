package org.qortal.test.common.transaction;

import org.qortal.account.PrivateKeyAccount;
import org.qortal.data.transaction.TransactionData;
import org.qortal.data.transaction.UpdateNameTransactionData;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;

public class UpdateNameTestTransaction extends TestTransaction {

	public static TransactionData randomTransaction(Repository repository, PrivateKeyAccount account, boolean wantValid) throws DataException {
		String newOwner = account.getAddress();
		String name = "test name";
		if (!wantValid)
			name += " " + random.nextInt(1_000_000);

		String newData = "{ \"key\": \"updated value\" }";

		return new UpdateNameTransactionData(generateBase(account), newOwner, name, newData);
	}

}

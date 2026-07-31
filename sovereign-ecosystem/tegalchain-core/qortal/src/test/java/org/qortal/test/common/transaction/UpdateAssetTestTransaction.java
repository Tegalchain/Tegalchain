package org.qortal.test.common.transaction;

import org.qortal.account.PrivateKeyAccount;
import org.qortal.data.transaction.TransactionData;
import org.qortal.data.transaction.UpdateAssetTransactionData;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;
import org.qortal.test.common.AssetUtils;

public class UpdateAssetTestTransaction extends TestTransaction {

	public static TransactionData randomTransaction(Repository repository, PrivateKeyAccount account, boolean wantValid) throws DataException {
		final long assetId = 1;
		String newOwner = account.getAddress();
		String newDescription = "updated random test asset";
		String newData = AssetUtils.randomData();

		return new UpdateAssetTransactionData(generateBase(account), assetId, newOwner, newDescription, newData);
	}

}

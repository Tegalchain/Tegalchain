package org.qortal.test.common;

import org.qortal.account.PrivateKeyAccount;
import org.qortal.data.transaction.BaseTransactionData;
import org.qortal.data.transaction.CreateGroupTransactionData;
import org.qortal.data.transaction.GroupApprovalTransactionData;
import org.qortal.data.transaction.JoinGroupTransactionData;
import org.qortal.data.transaction.TransactionData;
import org.qortal.group.Group;
import org.qortal.group.Group.ApprovalThreshold;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;
import org.qortal.transaction.Transaction.ApprovalStatus;
import org.qortal.utils.Amounts;

public class GroupUtils {

	public static final int txGroupId = Group.NO_GROUP;
	public static final long fee = 1L * Amounts.MULTIPLIER;

	public static int createGroup(Repository repository, String creatorAccountName, String groupName, boolean isOpen, ApprovalThreshold approvalThreshold,
				int minimumBlockDelay, int maximumBlockDelay) throws DataException {
		PrivateKeyAccount account = Common.getTestAccount(repository, creatorAccountName);

		byte[] reference = account.getLastReference();
		long timestamp = repository.getTransactionRepository().fromSignature(reference).getTimestamp() + 1;
		String groupDescription = groupName + " (test group)";

		BaseTransactionData baseTransactionData = new BaseTransactionData(timestamp, Group.NO_GROUP, reference, account.getPublicKey(), GroupUtils.fee, null);
		TransactionData transactionData = new CreateGroupTransactionData(baseTransactionData, groupName, groupDescription, isOpen, approvalThreshold, minimumBlockDelay, maximumBlockDelay);

		TransactionUtils.signAndMint(repository, transactionData, account);

		return repository.getGroupRepository().fromGroupName(groupName).getGroupId();
	}

	public static void joinGroup(Repository repository, String joinerAccountName, int groupId) throws DataException {
		PrivateKeyAccount account = Common.getTestAccount(repository, joinerAccountName);

		byte[] reference = account.getLastReference();
		long timestamp = repository.getTransactionRepository().fromSignature(reference).getTimestamp() + 1;

		BaseTransactionData baseTransactionData = new BaseTransactionData(timestamp, Group.NO_GROUP, reference, account.getPublicKey(), GroupUtils.fee, null);
		TransactionData transactionData = new JoinGroupTransactionData(baseTransactionData, groupId);

		TransactionUtils.signAndMint(repository, transactionData, account);
	}

	public static void approveTransaction(Repository repository, String accountName, byte[] pendingSignature, boolean decision) throws DataException {
		PrivateKeyAccount account = Common.getTestAccount(repository, accountName);

		byte[] reference = account.getLastReference();
		long timestamp = repository.getTransactionRepository().fromSignature(reference).getTimestamp() + 1;

		BaseTransactionData baseTransactionData = new BaseTransactionData(timestamp, Group.NO_GROUP, reference, account.getPublicKey(), GroupUtils.fee, null);
		TransactionData transactionData = new GroupApprovalTransactionData(baseTransactionData, pendingSignature, decision);

		TransactionUtils.signAndMint(repository, transactionData, account);
	}

	public static ApprovalStatus getApprovalStatus(Repository repository, byte[] signature) throws DataException {
		return repository.getTransactionRepository().fromSignature(signature).getApprovalStatus();
	}

	public static Integer getApprovalHeight(Repository repository, byte[] signature) throws DataException {
		return repository.getTransactionRepository().fromSignature(signature).getApprovalHeight();
	}

}

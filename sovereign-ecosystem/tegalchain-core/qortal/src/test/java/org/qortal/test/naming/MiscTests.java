package org.qortal.test.naming;

import static org.junit.Assert.*;

import java.util.List;

import org.junit.Before;
import org.junit.Test;
import org.qortal.account.PrivateKeyAccount;
import org.qortal.data.transaction.RegisterNameTransactionData;
import org.qortal.data.transaction.TransactionData;
import org.qortal.data.transaction.UpdateNameTransactionData;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;
import org.qortal.repository.RepositoryManager;
import org.qortal.test.common.Common;
import org.qortal.test.common.TransactionUtils;
import org.qortal.test.common.transaction.TestTransaction;
import org.qortal.transaction.Transaction;
import org.qortal.transaction.Transaction.ValidationResult;

public class MiscTests extends Common {

	@Before
	public void beforeTest() throws DataException {
		Common.useDefaultSettings();
	}

	@Test
	public void testGetRecentNames() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String name = "initial-name";
			String data = "initial-data";

			RegisterNameTransactionData transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), name, data);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			List<String> recentNames = repository.getNameRepository().getRecentNames(0L);

			assertNotNull(recentNames);
			assertFalse(recentNames.isEmpty());
		}
	}

	// test trying to register same name twice
	@Test
	public void testDuplicateRegisterName() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String name = "test-name";
			String data = "{}";

			RegisterNameTransactionData transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), name, data);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// duplicate
			String duplicateName = "TEST-nÁme";
			transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), duplicateName, data);
			Transaction transaction = Transaction.fromData(repository, transactionData);
			transaction.sign(alice);

			ValidationResult result = transaction.importAsUnconfirmed();
			assertTrue("Transaction should be invalid", ValidationResult.OK != result);
		}
	}

	// test register then trying to update another name to existing name
	@Test
	public void testUpdateToExistingName() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String name = "test-name";
			String data = "{}";

			TransactionData transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), name, data);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Register another name that we will later attempt to rename to first name (above)
			String otherName = "new-name";
			String otherData = "";
			transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), otherName, otherData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// we shouldn't be able to update name to existing name
			String duplicateName = "TEST-nÁme";
			transactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), otherName, duplicateName, otherData);
			Transaction transaction = Transaction.fromData(repository, transactionData);
			transaction.sign(alice);

			ValidationResult result = transaction.importAsUnconfirmed();
			assertTrue("Transaction should be invalid", ValidationResult.OK != result);
		}
	}

	// test trying to register a name that looks like an address
	@Test
	public void testRegisterAddressAsName() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String name = alice.getAddress();
			String data = "{}";

			RegisterNameTransactionData transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), name, data);
			Transaction transaction = Transaction.fromData(repository, transactionData);
			transaction.sign(alice);

			ValidationResult result = transaction.importAsUnconfirmed();
			assertTrue("Transaction should be invalid", ValidationResult.OK != result);
		}
	}

	// test register then trying to update to a name that looks like an address
	@Test
	public void testUpdateToAddressAsName() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String name = "test-name";
			String data = "{}";

			TransactionData transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), name, data);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// we shouldn't be able to update name to an address
			String newName = alice.getAddress();
			String newData = "";
			transactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), name, newName, newData);
			Transaction transaction = Transaction.fromData(repository, transactionData);
			transaction.sign(alice);

			ValidationResult result = transaction.importAsUnconfirmed();
			assertTrue("Transaction should be invalid", ValidationResult.OK != result);
		}
	}

}

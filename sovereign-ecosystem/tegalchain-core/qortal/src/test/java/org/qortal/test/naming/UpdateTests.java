package org.qortal.test.naming;

import static org.junit.Assert.*;

import org.junit.Before;
import org.junit.Test;
import org.qortal.account.PrivateKeyAccount;
import org.qortal.data.transaction.RegisterNameTransactionData;
import org.qortal.data.transaction.TransactionData;
import org.qortal.data.transaction.UpdateNameTransactionData;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;
import org.qortal.repository.RepositoryManager;
import org.qortal.test.common.BlockUtils;
import org.qortal.test.common.Common;
import org.qortal.test.common.TransactionUtils;
import org.qortal.test.common.transaction.TestTransaction;

public class UpdateTests extends Common {

	@Before
	public void beforeTest() throws DataException {
		Common.useDefaultSettings();
	}

	@Test
	public void testUpdateName() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String initialName = "initial-name";
			String initialData = "initial-data";

			TransactionData initialTransactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), initialName, initialData);
			TransactionUtils.signAndMint(repository, initialTransactionData, alice);

			String newName = "new-name";
			String newData = "";
			TransactionData updateTransactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), initialName, newName, newData);
			TransactionUtils.signAndMint(repository, updateTransactionData, alice);

			// Check old name no longer exists
			assertFalse(repository.getNameRepository().nameExists(initialName));

			// Check new name exists
			assertTrue(repository.getNameRepository().nameExists(newName));

			// Check updated timestamp is correct
			assertEquals((Long) updateTransactionData.getTimestamp(), repository.getNameRepository().fromName(newName).getUpdated());

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check new name no longer exists
			assertFalse(repository.getNameRepository().nameExists(newName));

			// Check old name exists again
			assertTrue(repository.getNameRepository().nameExists(initialName));

			// Check updated timestamp is empty
			assertNull(repository.getNameRepository().fromName(initialName).getUpdated());
		}
	}

	@Test
	public void testUpdateNameSameOwner() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String initialName = "initial-name";
			String initialData = "initial-data";

			TransactionData initialTransactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), initialName, initialData);
			TransactionUtils.signAndMint(repository, initialTransactionData, alice);

			String newName = "Initial-Name";
			String newData = "";
			TransactionData updateTransactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), initialName, newName, newData);
			TransactionUtils.signAndMint(repository, updateTransactionData, alice);

			// Check old name no longer exists
			assertFalse(repository.getNameRepository().nameExists(initialName));

			// Check new name exists
			assertTrue(repository.getNameRepository().nameExists(newName));

			// Check updated timestamp is correct
			assertEquals((Long) updateTransactionData.getTimestamp(), repository.getNameRepository().fromName(newName).getUpdated());

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check new name no longer exists
			assertFalse(repository.getNameRepository().nameExists(newName));

			// Check old name exists again
			assertTrue(repository.getNameRepository().nameExists(initialName));

			// Check updated timestamp is empty
			assertNull(repository.getNameRepository().fromName(initialName).getUpdated());
		}
	}

	// Test that reverting using previous UPDATE_NAME works as expected
	@Test
	public void testDoubleUpdateName() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String initialName = "initial-name";
			String initialData = "initial-data";

			TransactionData initialTransactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), initialName, initialData);
			TransactionUtils.signAndMint(repository, initialTransactionData, alice);

			String middleName = "middle-name";
			String middleData = "";
			TransactionData middleTransactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), initialName, middleName, middleData);
			TransactionUtils.signAndMint(repository, middleTransactionData, alice);

			// Check old name no longer exists
			assertFalse(repository.getNameRepository().nameExists(initialName));

			// Check new name exists
			assertTrue(repository.getNameRepository().nameExists(middleName));

			String newestName = "newest-name";
			String newestData = "newest-data";
			TransactionData newestTransactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), middleName, newestName, newestData);
			TransactionUtils.signAndMint(repository, newestTransactionData, alice);

			// Check previous name no longer exists
			assertFalse(repository.getNameRepository().nameExists(middleName));

			// Check newest name exists
			assertTrue(repository.getNameRepository().nameExists(newestName));

			// Check updated timestamp is correct
			assertEquals((Long) newestTransactionData.getTimestamp(), repository.getNameRepository().fromName(newestName).getUpdated());

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check newest name no longer exists
			assertFalse(repository.getNameRepository().nameExists(newestName));

			// Check previous name exists again
			assertTrue(repository.getNameRepository().nameExists(middleName));

			// Check updated timestamp is correct
			assertEquals((Long) middleTransactionData.getTimestamp(), repository.getNameRepository().fromName(middleName).getUpdated());

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check new name no longer exists
			assertFalse(repository.getNameRepository().nameExists(middleName));

			// Check original name exists again
			assertTrue(repository.getNameRepository().nameExists(initialName));

			// Check updated timestamp is empty
			assertNull(repository.getNameRepository().fromName(initialName).getUpdated());
		}
	}

	// Test that reverting using previous UPDATE_NAME works as expected
	@Test
	public void testIntermediateUpdateName() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String initialName = "initial-name";
			String initialData = "initial-data";

			TransactionData transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), initialName, initialData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Don't update name, but update data.
			// This tests whether reverting a future update/sale can find the correct previous name
			String middleName = "";
			String middleData = "middle-data";
			transactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), initialName, middleName, middleData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Check old name still exists
			assertTrue(repository.getNameRepository().nameExists(initialName));

			String newestName = "newest-name";
			String newestData = "newest-data";
			transactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), initialName, newestName, newestData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Check previous name no longer exists
			assertFalse(repository.getNameRepository().nameExists(initialName));

			// Check newest name exists
			assertTrue(repository.getNameRepository().nameExists(newestName));

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check original name exists again
			assertTrue(repository.getNameRepository().nameExists(initialName));

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check original name still exists
			assertTrue(repository.getNameRepository().nameExists(initialName));
		}
	}

	@Test
	public void testUpdateData() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String initialName = "initial-name";
			String initialData = "initial-data";

			TransactionData transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), initialName, initialData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			String newName = "";
			String newData = "new-data";
			transactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), initialName, newName, newData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Check name still exists
			assertTrue(repository.getNameRepository().nameExists(initialName));

			// Check data is correct
			assertEquals(newData, repository.getNameRepository().fromName(initialName).getData());

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check name still exists
			assertTrue(repository.getNameRepository().nameExists(initialName));

			// Check old data restored
			assertEquals(initialData, repository.getNameRepository().fromName(initialName).getData());
		}
	}

	// Test that reverting using previous UPDATE_NAME works as expected
	@Test
	public void testDoubleUpdateData() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String initialName = "initial-name";
			String initialData = "initial-data";

			TransactionData transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), initialName, initialData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Update data
			String middleName = "middle-name";
			String middleData = "middle-data";
			transactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), initialName, middleName, middleData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Check data is correct
			assertEquals(middleData, repository.getNameRepository().fromName(middleName).getData());

			String newestName = "newest-name";
			String newestData = "newest-data";
			transactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), middleName, newestName, newestData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Check data is correct
			assertEquals(newestData, repository.getNameRepository().fromName(newestName).getData());

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check data is correct
			assertEquals(middleData, repository.getNameRepository().fromName(middleName).getData());

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check data is correct
			assertEquals(initialData, repository.getNameRepository().fromName(initialName).getData());
		}
	}

	// Test that reverting using previous UPDATE_NAME works as expected
	@Test
	public void testIntermediateUpdateData() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			// Register-name
			PrivateKeyAccount alice = Common.getTestAccount(repository, "alice");
			String initialName = "initial-name";
			String initialData = "initial-data";

			TransactionData transactionData = new RegisterNameTransactionData(TestTransaction.generateBase(alice), initialName, initialData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Don't update data, but update name.
			// This tests whether reverting a future update/sale can find the correct previous data
			String middleName = "middle-name";
			String middleData = "";
			transactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), initialName, middleName, middleData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Check data is correct
			assertEquals(initialData, repository.getNameRepository().fromName(middleName).getData());

			String newestName = "newest-name";
			String newestData = "newest-data";
			transactionData = new UpdateNameTransactionData(TestTransaction.generateBase(alice), middleName, newestName, newestData);
			TransactionUtils.signAndMint(repository, transactionData, alice);

			// Check data is correct
			assertEquals(newestData, repository.getNameRepository().fromName(newestName).getData());

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check data is correct
			assertEquals(initialData, repository.getNameRepository().fromName(middleName).getData());

			// orphan and recheck
			BlockUtils.orphanLastBlock(repository);

			// Check data is correct
			assertEquals(initialData, repository.getNameRepository().fromName(initialName).getData());
		}
	}

}

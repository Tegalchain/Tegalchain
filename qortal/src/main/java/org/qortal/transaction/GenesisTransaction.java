package org.qortal.transaction;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import org.qortal.account.Account;
import org.qortal.account.PrivateKeyAccount;
import org.qortal.crypto.Crypto;
import org.qortal.data.transaction.GenesisTransactionData;
import org.qortal.data.transaction.TransactionData;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;
import org.qortal.transform.TransformationException;
import org.qortal.transform.transaction.TransactionTransformer;

import com.google.common.primitives.Bytes;

public class GenesisTransaction extends Transaction {

	// Properties
	private GenesisTransactionData genesisTransactionData;

	// Constructors

	public GenesisTransaction(Repository repository, TransactionData transactionData) {
		super(repository, transactionData);

		if (this.transactionData.getSignature() == null)
			this.transactionData.setSignature(this.calcSignature());

		this.genesisTransactionData = (GenesisTransactionData) this.transactionData;
	}

	// More information

	@Override
	public List<String> getRecipientAddresses() throws DataException {
		return Collections.singletonList(this.genesisTransactionData.getRecipient());
	}

	// Processing

	/**
	 * Refuse to calculate genesis transaction signature!
	 * <p>
	 * This is not possible as there is no private key for the genesis account and so no way to sign data.
	 * <p>
	 * <b>Always throws IllegalStateException.</b>
	 * 
	 * @throws IllegalStateException
	 */
	@Override
	public void sign(PrivateKeyAccount signer) {
		throw new IllegalStateException("There is no private key for genesis transactions");
	}

	/**
	 * Generate genesis transaction signature.
	 * <p>
	 * This is handled differently as there is no private key for the genesis account and so no way to sign data.
	 * <p>
	 * Instead we return the SHA-256 digest of the transaction, duplicated so that the returned byte[] is the same length as normal transaction signatures.
	 * 
	 * @return byte[]
	 */
	private byte[] calcSignature() {
		try {
			byte[] digest = Crypto.digest(TransactionTransformer.toBytes(this.transactionData));
			return Bytes.concat(digest, digest);
		} catch (TransformationException e) {
			return null;
		}
	}

	/**
	 * Check validity of genesis transaction signature.
	 * <p>
	 * This is handled differently as there is no private key for the genesis account and so no way to sign/verify data.
	 * <p>
	 * Instead we compared our signature with one generated by {@link GenesisTransaction#calcSignature()}.
	 * 
	 * @return boolean
	 */
	@Override
	public boolean isSignatureValid() {
		return Arrays.equals(this.transactionData.getSignature(), this.calcSignature());
	}

	@Override
	public ValidationResult isValid() {
		// Check amount is zero or positive
		if (this.genesisTransactionData.getAmount() < 0)
			return ValidationResult.NEGATIVE_AMOUNT;

		// Check recipient address is valid
		if (!Crypto.isValidAddress(this.genesisTransactionData.getRecipient()))
			return ValidationResult.INVALID_ADDRESS;

		return ValidationResult.OK;
	}

	@Override
	public void process() throws DataException {
		Account recipient = new Account(repository, this.genesisTransactionData.getRecipient());

		// Update recipient's balance
		recipient.setConfirmedBalance(this.genesisTransactionData.getAssetId(), this.genesisTransactionData.getAmount());
	}

	@Override
	public void processReferencesAndFees() throws DataException {
		// Do not attempt to update non-existent genesis account's reference!

		Account recipient = new Account(repository, this.genesisTransactionData.getRecipient());

		// Set recipient's starting reference (also creates account)
		recipient.setLastReference(this.genesisTransactionData.getSignature());
	}

	@Override
	public void orphan() throws DataException {
		// Delete recipient's account (and balance)
		this.repository.getAccountRepository().delete(this.genesisTransactionData.getRecipient());
	}

	@Override
	public void orphanReferencesAndFees() throws DataException {
		// Recipient's last reference removed thanks to delete() called by orphan() above.
	}

}

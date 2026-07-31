package org.qortal.account;

import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters;
import org.qortal.crypto.Crypto;
import org.qortal.data.account.AccountData;
import org.qortal.repository.Repository;

public class PublicKeyAccount extends Account {

	protected final byte[] publicKey;
	protected final Ed25519PublicKeyParameters edPublicKeyParams;

	public PublicKeyAccount(Repository repository, byte[] publicKey) {
		this(repository, new Ed25519PublicKeyParameters(publicKey, 0));
	}

	protected PublicKeyAccount(Repository repository, Ed25519PublicKeyParameters edPublicKeyParams) {
		super(repository, Crypto.toAddress(edPublicKeyParams.getEncoded()));

		this.edPublicKeyParams = edPublicKeyParams;
		this.publicKey = edPublicKeyParams.getEncoded();
	}

	protected PublicKeyAccount(Repository repository, byte[] publicKey, String address) {
		super(repository, address);

		this.publicKey = publicKey;
		this.edPublicKeyParams = null;
	}

	protected PublicKeyAccount() {
		this.publicKey = null;
		this.edPublicKeyParams = null;
	}

	public byte[] getPublicKey() {
		return this.publicKey;
	}

	@Override
	protected AccountData buildAccountData() {
		AccountData accountData = super.buildAccountData();
		accountData.setPublicKey(this.publicKey);
		return accountData;
	}

	public boolean verify(byte[] signature, byte[] message) {
		return Crypto.verify(this.publicKey, signature, message);
	}

	public static String getAddress(byte[] publicKey) {
		return Crypto.toAddress(publicKey);
	}

}

package org.qortal.api.model;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;

import org.qortal.crypto.Crypto;

@XmlAccessorType(XmlAccessType.FIELD)
public class BlockSignerSummary {

	// Properties

	public int blockCount;

	public byte[] mintingAccountPublicKey;
	public String mintingAccount;

	public byte[] rewardSharePublicKey;
	public String recipientAccount;

	// Constructors

	protected BlockSignerSummary() {
	}

	/** Constructs BlockSignerSummary in non-reward-share context. */
	public BlockSignerSummary(byte[] blockMinterPublicKey, int blockCount) {
		this.blockCount = blockCount;

		this.mintingAccountPublicKey = blockMinterPublicKey;
		this.mintingAccount = Crypto.toAddress(this.mintingAccountPublicKey);
	}

	/** Constructs BlockSignerSummary in reward-share context. */
	public BlockSignerSummary(byte[] rewardSharePublicKey, int blockCount, byte[] mintingAccountPublicKey, String minterAccount, String recipientAccount) {
		this.rewardSharePublicKey = rewardSharePublicKey;
		this.blockCount = blockCount;

		this.mintingAccountPublicKey = mintingAccountPublicKey;
		this.mintingAccount = minterAccount;

		this.recipientAccount = recipientAccount;
	}

}

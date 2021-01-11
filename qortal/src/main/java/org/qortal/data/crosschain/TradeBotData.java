package org.qortal.data.crosschain;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlTransient;
import javax.xml.bind.annotation.adapters.XmlJavaTypeAdapter;

import io.swagger.v3.oas.annotations.media.Schema;

// All properties to be converted to JSON via JAXB
@XmlAccessorType(XmlAccessType.FIELD)
public class TradeBotData {

	private byte[] tradePrivateKey;

	private String acctName;
	private String tradeState;

	// Internal use - not shown via API
	@XmlTransient
	@Schema(hidden = true)
	private int tradeStateValue;

	private String creatorAddress;
	private String atAddress;

	private long timestamp;

	@XmlJavaTypeAdapter(value = org.qortal.api.AmountTypeAdapter.class)
	private long qortAmount;

	private byte[] tradeNativePublicKey;
	private byte[] tradeNativePublicKeyHash;
	String tradeNativeAddress;

	private byte[] secret;
	private byte[] hashOfSecret;

	private String foreignBlockchain;
	private byte[] tradeForeignPublicKey;
	private byte[] tradeForeignPublicKeyHash;

	@Deprecated
	@Schema(description = "DEPRECATED: use foreignAmount instead", type = "number")
	@XmlJavaTypeAdapter(value = org.qortal.api.AmountTypeAdapter.class)
	private long bitcoinAmount;

	@Schema(description = "amount in foreign blockchain currency", type = "number")
	@XmlJavaTypeAdapter(value = org.qortal.api.AmountTypeAdapter.class)
	private long foreignAmount;

	// Never expose this via API
	@XmlTransient
	@Schema(hidden = true)
	private String foreignKey;

	private byte[] lastTransactionSignature;
	private Integer lockTimeA;

	// Could be Bitcoin or Qortal...
	private byte[] receivingAccountInfo;

	protected TradeBotData() {
		/* JAXB */
	}

	public TradeBotData(byte[] tradePrivateKey, String acctName, String tradeState, int tradeStateValue,
			String creatorAddress, String atAddress,
			long timestamp, long qortAmount,
			byte[] tradeNativePublicKey, byte[] tradeNativePublicKeyHash, String tradeNativeAddress,
			byte[] secret, byte[] hashOfSecret,
			String foreignBlockchain, byte[] tradeForeignPublicKey, byte[] tradeForeignPublicKeyHash,
			long foreignAmount, String foreignKey,
			byte[] lastTransactionSignature, Integer lockTimeA, byte[] receivingAccountInfo) {
		this.tradePrivateKey = tradePrivateKey;
		this.acctName = acctName;
		this.tradeState = tradeState;
		this.tradeStateValue = tradeStateValue;
		this.creatorAddress = creatorAddress;
		this.atAddress = atAddress;
		this.timestamp = timestamp;
		this.qortAmount = qortAmount;
		this.tradeNativePublicKey = tradeNativePublicKey;
		this.tradeNativePublicKeyHash = tradeNativePublicKeyHash;
		this.tradeNativeAddress = tradeNativeAddress;
		this.secret = secret;
		this.hashOfSecret = hashOfSecret;
		this.foreignBlockchain = foreignBlockchain;
		this.tradeForeignPublicKey = tradeForeignPublicKey;
		this.tradeForeignPublicKeyHash = tradeForeignPublicKeyHash;
		// deprecated copy
		this.bitcoinAmount = foreignAmount;
		this.foreignAmount = foreignAmount;
		this.foreignKey = foreignKey;
		this.lastTransactionSignature = lastTransactionSignature;
		this.lockTimeA = lockTimeA;
		this.receivingAccountInfo = receivingAccountInfo;
	}

	public byte[] getTradePrivateKey() {
		return this.tradePrivateKey;
	}

	public String getAcctName() {
		return this.acctName;
	}

	public String getState() {
		return this.tradeState;
	}

	public void setState(String state) {
		this.tradeState = state;
	}

	public int getStateValue() {
		return this.tradeStateValue;
	}

	public void setStateValue(int stateValue) {
		this.tradeStateValue = stateValue;
	}

	public String getCreatorAddress() {
		return this.creatorAddress;
	}

	public String getAtAddress() {
		return this.atAddress;
	}

	public void setAtAddress(String atAddress) {
		this.atAddress = atAddress;
	}

	public long getTimestamp() {
		return this.timestamp;
	}

	public void setTimestamp(long timestamp) {
		this.timestamp = timestamp;
	}

	public long getQortAmount() {
		return this.qortAmount;
	}

	public byte[] getTradeNativePublicKey() {
		return this.tradeNativePublicKey;
	}

	public byte[] getTradeNativePublicKeyHash() {
		return this.tradeNativePublicKeyHash;
	}

	public String getTradeNativeAddress() {
		return this.tradeNativeAddress;
	}

	public byte[] getSecret() {
		return this.secret;
	}

	public byte[] getHashOfSecret() {
		return this.hashOfSecret;
	}

	public String getForeignBlockchain() {
		return this.foreignBlockchain;
	}

	public byte[] getTradeForeignPublicKey() {
		return this.tradeForeignPublicKey;
	}

	public byte[] getTradeForeignPublicKeyHash() {
		return this.tradeForeignPublicKeyHash;
	}

	public long getForeignAmount() {
		return this.foreignAmount;
	}

	public String getForeignKey() {
		return this.foreignKey;
	}

	public byte[] getLastTransactionSignature() {
		return this.lastTransactionSignature;
	}

	public void setLastTransactionSignature(byte[] lastTransactionSignature) {
		this.lastTransactionSignature = lastTransactionSignature;
	}

	public Integer getLockTimeA() {
		return this.lockTimeA;
	}

	public void setLockTimeA(Integer lockTimeA) {
		this.lockTimeA = lockTimeA;
	}

	public byte[] getReceivingAccountInfo() {
		return this.receivingAccountInfo;
	}

	// Mostly for debugging
	public String toString() {
		return String.format("%s: %s (%d)", this.atAddress, this.tradeState, this.tradeStateValue);
	}

}

package org.qortal.data.network;

import java.util.Arrays;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;

import org.qortal.account.PublicKeyAccount;

// All properties to be converted to JSON via JAXB
@XmlAccessorType(XmlAccessType.FIELD)
public class OnlineAccountData {

	protected long timestamp;
	protected byte[] signature;
	protected byte[] publicKey;

	// Constructors

	// necessary for JAXB serialization
	protected OnlineAccountData() {
	}

	public OnlineAccountData(long timestamp, byte[] signature, byte[] publicKey) {
		this.timestamp = timestamp;
		this.signature = signature;
		this.publicKey = publicKey;
	}

	public long getTimestamp() {
		return this.timestamp;
	}

	public byte[] getSignature() {
		return this.signature;
	}

	public byte[] getPublicKey() {
		return this.publicKey;
	}

	// For JAXB
	@XmlElement(name = "address")
	protected String getAddress() {
		return new PublicKeyAccount(null, this.publicKey).getAddress();
	}

	// Comparison

	@Override
	public boolean equals(Object other) {
		if (other == this)
			return true;

		if (!(other instanceof OnlineAccountData))
			return false;

		OnlineAccountData otherOnlineAccountData = (OnlineAccountData) other;

		// Very quick comparison
		if (otherOnlineAccountData.timestamp != this.timestamp)
			return false;

		// Signature more likely to be unique than public key
		if (!Arrays.equals(otherOnlineAccountData.signature, this.signature))
			return false;

		if (!Arrays.equals(otherOnlineAccountData.publicKey, this.publicKey))
			return false;

		return true;
	}

	@Override
	public int hashCode() {
		// Pretty lazy implementation
		return (int) this.timestamp;
	}

}

package org.qortal.data.at;

public class ATStateData {

	// Properties
	private String ATAddress;
	private Integer height;
	private byte[] stateData;
	private byte[] stateHash;
	private Long fees;
	private boolean isInitial;

	// Constructors

	/** Create new ATStateData */
	public ATStateData(String ATAddress, Integer height, byte[] stateData, byte[] stateHash, Long fees, boolean isInitial) {
		this.ATAddress = ATAddress;
		this.height = height;
		this.stateData = stateData;
		this.stateHash = stateHash;
		this.fees = fees;
		this.isInitial = isInitial;
	}

	/** For recreating per-block ATStateData from repository where not all info is needed */
	public ATStateData(String ATAddress, int height, byte[] stateHash, Long fees, boolean isInitial) {
		this(ATAddress, height, null, stateHash, fees, isInitial);
	}

	/** For creating ATStateData from serialized bytes when we don't have all the info */
	public ATStateData(String ATAddress, byte[] stateHash) {
		// This won't ever be initial AT state from deployment as that's never serialized over the network,
		// but generated when the DeployAtTransaction is processed locally.
		this(ATAddress, null, null, stateHash, null, false);
	}

	/** For creating ATStateData from serialized bytes when we don't have all the info */
	public ATStateData(String ATAddress, byte[] stateHash, Long fees) {
		// This won't ever be initial AT state from deployment as that's never serialized over the network,
		// but generated when the DeployAtTransaction is processed locally.
		this(ATAddress, null, null, stateHash, fees, false);
	}

	// Getters / setters

	public String getATAddress() {
		return this.ATAddress;
	}

	public Integer getHeight() {
		return this.height;
	}

	// Likely to be used when block received over network is attached to blockchain
	public void setHeight(Integer height) {
		this.height = height;
	}

	public byte[] getStateData() {
		return this.stateData;
	}

	public byte[] getStateHash() {
		return this.stateHash;
	}

	public Long getFees() {
		return this.fees;
	}

	public boolean isInitial() {
		return this.isInitial;
	}

}

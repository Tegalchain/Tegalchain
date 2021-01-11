package org.qortal.data.network;

public class PeerChainTipData {

	/** Latest block height as reported by peer. */
	private Integer lastHeight;
	/** Latest block signature as reported by peer. */
	private byte[] lastBlockSignature;
	/** Latest block timestamp as reported by peer. */
	private Long lastBlockTimestamp;
	/** Latest block minter public key as reported by peer. */
	private byte[] lastBlockMinter;

	public PeerChainTipData(Integer lastHeight, byte[] lastBlockSignature, Long lastBlockTimestamp, byte[] lastBlockMinter) {
		this.lastHeight = lastHeight;
		this.lastBlockSignature = lastBlockSignature;
		this.lastBlockTimestamp = lastBlockTimestamp;
		this.lastBlockMinter = lastBlockMinter;
	}

	public Integer getLastHeight() {
		return this.lastHeight;
	}

	public byte[] getLastBlockSignature() {
		return this.lastBlockSignature;
	}

	public Long getLastBlockTimestamp() {
		return this.lastBlockTimestamp;
	}

	public byte[] getLastBlockMinter() {
		return this.lastBlockMinter;
	}

}

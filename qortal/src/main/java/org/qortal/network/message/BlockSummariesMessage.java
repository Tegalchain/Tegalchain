package org.qortal.network.message;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.List;

import org.qortal.data.block.BlockSummaryData;
import org.qortal.transform.Transformer;
import org.qortal.transform.block.BlockTransformer;

import com.google.common.primitives.Ints;

public class BlockSummariesMessage extends Message {

	private static final int BLOCK_SUMMARY_LENGTH = BlockTransformer.BLOCK_SIGNATURE_LENGTH + Transformer.INT_LENGTH + Transformer.PUBLIC_KEY_LENGTH + Transformer.INT_LENGTH;

	private List<BlockSummaryData> blockSummaries;

	public BlockSummariesMessage(List<BlockSummaryData> blockSummaries) {
		this(-1, blockSummaries);
	}

	private BlockSummariesMessage(int id, List<BlockSummaryData> blockSummaries) {
		super(id, MessageType.BLOCK_SUMMARIES);

		this.blockSummaries = blockSummaries;
	}

	public List<BlockSummaryData> getBlockSummaries() {
		return this.blockSummaries;
	}

	public static Message fromByteBuffer(int id, ByteBuffer bytes) throws UnsupportedEncodingException {
		int count = bytes.getInt();

		if (bytes.remaining() != count * BLOCK_SUMMARY_LENGTH)
			return null;

		List<BlockSummaryData> blockSummaries = new ArrayList<>();
		for (int i = 0; i < count; ++i) {
			int height = bytes.getInt();

			byte[] signature = new byte[BlockTransformer.BLOCK_SIGNATURE_LENGTH];
			bytes.get(signature);

			byte[] minterPublicKey = new byte[Transformer.PUBLIC_KEY_LENGTH];
			bytes.get(minterPublicKey);

			int onlineAccountsCount = bytes.getInt();

			BlockSummaryData blockSummary = new BlockSummaryData(height, signature, minterPublicKey, onlineAccountsCount);
			blockSummaries.add(blockSummary);
		}

		return new BlockSummariesMessage(id, blockSummaries);
	}

	@Override
	protected byte[] toData() {
		try {
			ByteArrayOutputStream bytes = new ByteArrayOutputStream();

			bytes.write(Ints.toByteArray(this.blockSummaries.size()));

			for (BlockSummaryData blockSummary : this.blockSummaries) {
				bytes.write(Ints.toByteArray(blockSummary.getHeight()));
				bytes.write(blockSummary.getSignature());
				bytes.write(blockSummary.getMinterPublicKey());
				bytes.write(Ints.toByteArray(blockSummary.getOnlineAccountsCount()));
			}

			return bytes.toByteArray();
		} catch (IOException e) {
			return null;
		}
	}

}

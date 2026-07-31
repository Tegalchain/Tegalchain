package org.qortal.api.resource;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.ArraySchema;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;

import java.util.ArrayList;
import java.util.List;

import javax.servlet.http.HttpServletRequest;

import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.QueryParam;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.MediaType;

import org.qortal.api.ApiError;
import org.qortal.api.ApiErrors;
import org.qortal.api.ApiExceptionFactory;
import org.qortal.api.model.BlockSignerSummary;
import org.qortal.crypto.Crypto;
import org.qortal.data.account.AccountData;
import org.qortal.data.block.BlockData;
import org.qortal.data.block.BlockSummaryData;
import org.qortal.data.transaction.TransactionData;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;
import org.qortal.repository.RepositoryManager;
import org.qortal.utils.Base58;

@Path("/blocks")
@Tag(name = "Blocks")
public class BlocksResource {

	@Context
	HttpServletRequest request;

	@GET
	@Path("/signature/{signature}")
	@Operation(
		summary = "Fetch block using base58 signature",
		description = "Returns the block that matches the given signature",
		responses = {
			@ApiResponse(
				description = "the block",
				content = @Content(
					schema = @Schema(
						implementation = BlockData.class
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.INVALID_SIGNATURE, ApiError.BLOCK_UNKNOWN, ApiError.REPOSITORY_ISSUE
	})
	public BlockData getBlock(@PathParam("signature") String signature58) {
		// Decode signature
		byte[] signature;
		try {
			signature = Base58.decode(signature58);
		} catch (NumberFormatException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_SIGNATURE, e);
		}

		try (final Repository repository = RepositoryManager.getRepository()) {
			BlockData blockData = repository.getBlockRepository().fromSignature(signature);
			if (blockData == null)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.BLOCK_UNKNOWN);

			return blockData;
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/signature/{signature}/transactions")
	@Operation(
		summary = "Fetch block using base58 signature",
		description = "Returns the block that matches the given signature",
		responses = {
			@ApiResponse(
				description = "the block",
				content = @Content(
					array = @ArraySchema(
						schema = @Schema(
							implementation = TransactionData.class
						)
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.INVALID_SIGNATURE, ApiError.BLOCK_UNKNOWN, ApiError.REPOSITORY_ISSUE
	})
	public List<TransactionData> getBlockTransactions(@PathParam("signature") String signature58, @Parameter(
		ref = "limit"
	) @QueryParam("limit") Integer limit, @Parameter(
		ref = "offset"
	) @QueryParam("offset") Integer offset, @Parameter(
		ref = "reverse"
	) @QueryParam("reverse") Boolean reverse) {
		// Decode signature
		byte[] signature;
		try {
			signature = Base58.decode(signature58);
		} catch (NumberFormatException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_SIGNATURE, e);
		}

		try (final Repository repository = RepositoryManager.getRepository()) {
			if (repository.getBlockRepository().getHeightFromSignature(signature) == 0)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.BLOCK_UNKNOWN);

			return repository.getBlockRepository().getTransactionsFromSignature(signature, limit, offset, reverse);
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/first")
	@Operation(
		summary = "Fetch genesis block",
		description = "Returns the genesis block",
		responses = {
			@ApiResponse(
				description = "the block",
				content = @Content(
					schema = @Schema(
						implementation = BlockData.class
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.REPOSITORY_ISSUE
	})
	public BlockData getFirstBlock() {
		try (final Repository repository = RepositoryManager.getRepository()) {
			return repository.getBlockRepository().fromHeight(1);
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/last")
	@Operation(
		summary = "Fetch last/newest block in blockchain",
		description = "Returns the last valid block",
		responses = {
			@ApiResponse(
				description = "the block",
				content = @Content(
					schema = @Schema(
						implementation = BlockData.class
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.REPOSITORY_ISSUE
	})
	public BlockData getLastBlock() {
		try (final Repository repository = RepositoryManager.getRepository()) {
			return repository.getBlockRepository().getLastBlock();
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/child/{signature}")
	@Operation(
		summary = "Fetch child block using base58 signature of parent block",
		description = "Returns the child block of the block that matches the given signature",
		responses = {
			@ApiResponse(
				description = "the block",
				content = @Content(
					schema = @Schema(
						implementation = BlockData.class
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.INVALID_SIGNATURE, ApiError.BLOCK_UNKNOWN, ApiError.REPOSITORY_ISSUE
	})
	public BlockData getChild(@PathParam("signature") String signature58) {
		// Decode signature
		byte[] signature;
		try {
			signature = Base58.decode(signature58);
		} catch (NumberFormatException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_SIGNATURE, e);
		}

		try (final Repository repository = RepositoryManager.getRepository()) {
			BlockData blockData = repository.getBlockRepository().fromSignature(signature);

			// Check block exists
			if (blockData == null)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.BLOCK_UNKNOWN);

			BlockData childBlockData = repository.getBlockRepository().fromReference(signature);

			// Check child block exists
			if (childBlockData == null)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.BLOCK_UNKNOWN);

			return childBlockData;
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/height")
	@Operation(
		summary = "Current blockchain height",
		description = "Returns the block height of the last block.",
		responses = {
			@ApiResponse(
				description = "the height",
				content = @Content(
					mediaType = MediaType.TEXT_PLAIN,
					schema = @Schema(
						type = "number"
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.REPOSITORY_ISSUE
	})
	public int getHeight() {
		try (final Repository repository = RepositoryManager.getRepository()) {
			return repository.getBlockRepository().getBlockchainHeight();
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/height/{signature}")
	@Operation(
		summary = "Height of specific block",
		description = "Returns the block height of the block that matches the given signature",
		responses = {
			@ApiResponse(
				description = "the height",
				content = @Content(
					mediaType = MediaType.TEXT_PLAIN,
					schema = @Schema(
						type = "number"
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.INVALID_SIGNATURE, ApiError.BLOCK_UNKNOWN, ApiError.REPOSITORY_ISSUE
	})
	public int getHeight(@PathParam("signature") String signature58) {
		// Decode signature
		byte[] signature;
		try {
			signature = Base58.decode(signature58);
		} catch (NumberFormatException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_SIGNATURE, e);
		}

		try (final Repository repository = RepositoryManager.getRepository()) {
			BlockData blockData = repository.getBlockRepository().fromSignature(signature);

			// Check block exists
			if (blockData == null)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.BLOCK_UNKNOWN);

			return blockData.getHeight();
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/byheight/{height}")
	@Operation(
		summary = "Fetch block using block height",
		description = "Returns the block with given height",
		responses = {
			@ApiResponse(
				description = "the block",
				content = @Content(
					schema = @Schema(
						implementation = BlockData.class
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.BLOCK_UNKNOWN, ApiError.REPOSITORY_ISSUE
	})
	public BlockData getByHeight(@PathParam("height") int height) {
		try (final Repository repository = RepositoryManager.getRepository()) {
			BlockData blockData = repository.getBlockRepository().fromHeight(height);
			if (blockData == null)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.BLOCK_UNKNOWN);

			return blockData;
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/timestamp/{timestamp}")
	@Operation(
		summary = "Fetch nearest block before given timestamp",
		responses = {
			@ApiResponse(
				description = "the block",
				content = @Content(
					schema = @Schema(
						implementation = BlockData.class
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.BLOCK_UNKNOWN, ApiError.REPOSITORY_ISSUE
	})
	public BlockData getByTimestamp(@PathParam("timestamp") long timestamp) {
		try (final Repository repository = RepositoryManager.getRepository()) {
			int height = repository.getBlockRepository().getHeightFromTimestamp(timestamp);
			if (height == 0)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.BLOCK_UNKNOWN);

			BlockData blockData = repository.getBlockRepository().fromHeight(height);
			if (blockData == null)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.BLOCK_UNKNOWN);

			return blockData;
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/range/{height}")
	@Operation(
		summary = "Fetch blocks starting with given height",
		description = "Returns blocks starting with given height.",
		responses = {
			@ApiResponse(
				description = "blocks",
				content = @Content(
					array = @ArraySchema(
						schema = @Schema(
							implementation = BlockData.class
						)
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.REPOSITORY_ISSUE
	})
	public List<BlockData> getBlockRange(@PathParam("height") int height, @Parameter(
		ref = "count"
	) @QueryParam("count") int count) {
		try (final Repository repository = RepositoryManager.getRepository()) {
			List<BlockData> blocks = new ArrayList<>();

			for (/* count already set */; count > 0; --count, ++height) {
				BlockData blockData = repository.getBlockRepository().fromHeight(height);
				if (blockData == null)
					// Run out of blocks!
					break;

				blocks.add(blockData);
			}

			return blocks;
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/signer/{address}")
	@Operation(
		summary = "Fetch block summaries for blocks signed by address",
		responses = {
			@ApiResponse(
				description = "block summaries",
				content = @Content(
					array = @ArraySchema(
						schema = @Schema(
							implementation = BlockSummaryData.class
						)
					)
				)
			)
		}
	)
	@ApiErrors({ApiError.INVALID_ADDRESS, ApiError.PUBLIC_KEY_NOT_FOUND, ApiError.REPOSITORY_ISSUE})
	public List<BlockSummaryData> getBlockSummariesBySigner(@PathParam("address") String address, @Parameter(
			ref = "limit"
			) @QueryParam("limit") Integer limit, @Parameter(
				ref = "offset"
			) @QueryParam("offset") Integer offset, @Parameter(
				ref = "reverse"
			) @QueryParam("reverse") Boolean reverse) {
		if (!Crypto.isValidAddress(address))
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_ADDRESS);

		try (final Repository repository = RepositoryManager.getRepository()) {
			// Get public key from address
			AccountData accountData = repository.getAccountRepository().getAccount(address);
			if (accountData == null || accountData.getPublicKey() == null)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.PUBLIC_KEY_NOT_FOUND);

			return repository.getBlockRepository().getBlockSummariesBySigner(accountData.getPublicKey(), limit, offset, reverse);
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/signers")
	@Operation(
		summary = "Show summary of block signers",
		description = "Returns count of blocks signed, optionally limited to minters/recipients in passed address(es).",
		responses = {
			@ApiResponse(
				content = @Content(
					array = @ArraySchema(
						schema = @Schema(
							implementation = BlockSignerSummary.class
						)
					)
				)
			)
		}
	)
	public List<BlockSignerSummary> getBlockSigners(@QueryParam("address") List<String> addresses,
			@Parameter(
				ref = "limit"
			) @QueryParam("limit") Integer limit, @Parameter(
				ref = "offset"
			) @QueryParam("offset") Integer offset, @Parameter(
				ref = "reverse"
			) @QueryParam("reverse") Boolean reverse) {
		try (final Repository repository = RepositoryManager.getRepository()) {
			for (String address : addresses)
				if (!Crypto.isValidAddress(address))
					throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_ADDRESS);

			return repository.getBlockRepository().getBlockSigners(addresses, limit, offset, reverse);
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

	@GET
	@Path("/summaries")
	@Operation(
		summary = "Fetch only summary info about a range of blocks",
		description = "Specify up to 2 out 3 of: start, end and count. If neither start nor end are specified, then end is assumed to be latest block. Where necessary, count is assumed to be 50.",
		responses = {
			@ApiResponse(
				description = "blocks",
				content = @Content(
					array = @ArraySchema(
						schema = @Schema(
							implementation = BlockSummaryData.class
						)
					)
				)
			)
		}
	)
	@ApiErrors({
		ApiError.REPOSITORY_ISSUE
	})
	public List<BlockSummaryData> getBlockSummaries(
			@QueryParam("start") Integer startHeight,
			@QueryParam("end") Integer endHeight,
			@Parameter(ref = "count") @QueryParam("count") Integer count) {
		// Check up to 2 out of 3 params
		if (startHeight != null && endHeight != null && count != null)
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_CRITERIA);

		// Check values
		if ((startHeight != null && startHeight < 1) || (endHeight != null && endHeight < 1) || (count != null && count < 1))
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_CRITERIA);

		try (final Repository repository = RepositoryManager.getRepository()) {
			return repository.getBlockRepository().getBlockSummaries(startHeight, endHeight, count);
		} catch (DataException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.REPOSITORY_ISSUE, e);
		}
	}

}

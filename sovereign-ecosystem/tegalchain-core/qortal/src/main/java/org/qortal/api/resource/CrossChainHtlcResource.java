package org.qortal.api.resource;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;

import java.math.BigDecimal;
import java.util.List;

import javax.servlet.http.HttpServletRequest;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.MediaType;

import org.bitcoinj.core.TransactionOutput;
import org.qortal.api.ApiError;
import org.qortal.api.ApiErrors;
import org.qortal.api.ApiExceptionFactory;
import org.qortal.api.Security;
import org.qortal.api.model.CrossChainBitcoinyHTLCStatus;
import org.qortal.crosschain.Bitcoiny;
import org.qortal.crosschain.ForeignBlockchainException;
import org.qortal.crosschain.SupportedBlockchain;
import org.qortal.crosschain.BitcoinyHTLC;
import org.qortal.utils.NTP;

import com.google.common.hash.HashCode;

@Path("/crosschain/htlc")
@Tag(name = "Cross-Chain (Hash time-locked contracts)")
public class CrossChainHtlcResource {

	@Context
	HttpServletRequest request;

	@GET
	@Path("/address/{blockchain}/{refundPKH}/{locktime}/{redeemPKH}/{hashOfSecret}")
	@Operation(
		summary = "Returns HTLC address based on trade info",
		description = "Blockchain can be BITCOIN or LITECOIN. Public key hashes (PKH) and hash of secret should be 20 bytes (hex). Locktime is seconds since epoch.",
		responses = {
			@ApiResponse(
				content = @Content(mediaType = MediaType.TEXT_PLAIN, schema = @Schema(type = "string"))
			)
		}
	)
	@ApiErrors({ApiError.INVALID_PUBLIC_KEY, ApiError.INVALID_CRITERIA})
	public String deriveHtlcAddress(@PathParam("blockchain") String blockchainName,
			@PathParam("refundPKH") String refundHex,
			@PathParam("locktime") int lockTime,
			@PathParam("redeemPKH") String redeemHex,
			@PathParam("hashOfSecret") String hashOfSecretHex) {
		SupportedBlockchain blockchain = SupportedBlockchain.valueOf(blockchainName);
		if (blockchain == null)
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_CRITERIA);

		byte[] refunderPubKeyHash;
		byte[] redeemerPubKeyHash;
		byte[] hashOfSecret;

		try {
			refunderPubKeyHash = HashCode.fromString(refundHex).asBytes();
			redeemerPubKeyHash = HashCode.fromString(redeemHex).asBytes();

			if (refunderPubKeyHash.length != 20 || redeemerPubKeyHash.length != 20)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_PUBLIC_KEY);
		} catch (IllegalArgumentException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_PUBLIC_KEY);
		}

		try {
			hashOfSecret = HashCode.fromString(hashOfSecretHex).asBytes();
			if (hashOfSecret.length != 20)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_CRITERIA);
		} catch (IllegalArgumentException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_CRITERIA);
		}

		byte[] redeemScript = BitcoinyHTLC.buildScript(refunderPubKeyHash, lockTime, redeemerPubKeyHash, hashOfSecret);

		Bitcoiny bitcoiny = (Bitcoiny) blockchain.getInstance();

		return bitcoiny.deriveP2shAddress(redeemScript);
	}

	@GET
	@Path("/status/{blockchain}/{refundPKH}/{locktime}/{redeemPKH}/{hashOfSecret}")
	@Operation(
		summary = "Checks HTLC status",
		description = "Blockchain can be BITCOIN or LITECOIN. Public key hashes (PKH) and hash of secret should be 20 bytes (hex). Locktime is seconds since epoch.",
		responses = {
			@ApiResponse(
				content = @Content(mediaType = MediaType.APPLICATION_JSON, schema = @Schema(implementation = CrossChainBitcoinyHTLCStatus.class))
			)
		}
	)
	@ApiErrors({ApiError.INVALID_CRITERIA, ApiError.INVALID_ADDRESS, ApiError.ADDRESS_UNKNOWN})
	public CrossChainBitcoinyHTLCStatus checkHtlcStatus(@PathParam("blockchain") String blockchainName,
			@PathParam("refundPKH") String refundHex,
			@PathParam("locktime") int lockTime,
			@PathParam("redeemPKH") String redeemHex,
			@PathParam("hashOfSecret") String hashOfSecretHex) {
		Security.checkApiCallAllowed(request);

		SupportedBlockchain blockchain = SupportedBlockchain.valueOf(blockchainName);
		if (blockchain == null)
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_CRITERIA);

		byte[] refunderPubKeyHash;
		byte[] redeemerPubKeyHash;
		byte[] hashOfSecret;

		try {
			refunderPubKeyHash = HashCode.fromString(refundHex).asBytes();
			redeemerPubKeyHash = HashCode.fromString(redeemHex).asBytes();

			if (refunderPubKeyHash.length != 20 || redeemerPubKeyHash.length != 20)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_PUBLIC_KEY);
		} catch (IllegalArgumentException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_PUBLIC_KEY);
		}

		try {
			hashOfSecret = HashCode.fromString(hashOfSecretHex).asBytes();
			if (hashOfSecret.length != 20)
				throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_CRITERIA);
		} catch (IllegalArgumentException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.INVALID_CRITERIA);
		}

		byte[] redeemScript = BitcoinyHTLC.buildScript(refunderPubKeyHash, lockTime, redeemerPubKeyHash, hashOfSecret);

		Bitcoiny bitcoiny = (Bitcoiny) blockchain.getInstance();

		String p2shAddress = bitcoiny.deriveP2shAddress(redeemScript);

		long now = NTP.getTime();

		try {
			int medianBlockTime = bitcoiny.getMedianBlockTime();

			// Check P2SH is funded
			long p2shBalance = bitcoiny.getConfirmedBalance(p2shAddress.toString());

			CrossChainBitcoinyHTLCStatus htlcStatus = new CrossChainBitcoinyHTLCStatus();
			htlcStatus.bitcoinP2shAddress = p2shAddress;
			htlcStatus.bitcoinP2shBalance = BigDecimal.valueOf(p2shBalance, 8);

			List<TransactionOutput> fundingOutputs = bitcoiny.getUnspentOutputs(p2shAddress.toString());

			if (p2shBalance > 0L && !fundingOutputs.isEmpty()) {
				htlcStatus.canRedeem = now >= medianBlockTime * 1000L;
				htlcStatus.canRefund = now >= lockTime * 1000L;
			}

			if (now >= medianBlockTime * 1000L) {
				// See if we can extract secret
				htlcStatus.secret = BitcoinyHTLC.findHtlcSecret(bitcoiny, htlcStatus.bitcoinP2shAddress);
			}

			return htlcStatus;
		} catch (ForeignBlockchainException e) {
			throw ApiExceptionFactory.INSTANCE.createException(request, ApiError.FOREIGN_BLOCKCHAIN_NETWORK_ISSUE);
		}
	}

	// TODO: refund

	// TODO: redeem

}
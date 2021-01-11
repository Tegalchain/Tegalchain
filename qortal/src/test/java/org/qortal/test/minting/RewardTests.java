package org.qortal.test.minting;

import static org.junit.Assert.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.bitcoinj.core.Base58;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.qortal.account.PrivateKeyAccount;
import org.qortal.asset.Asset;
import org.qortal.block.BlockChain;
import org.qortal.block.BlockChain.RewardByHeight;
import org.qortal.controller.BlockMinter;
import org.qortal.data.account.AccountBalanceData;
import org.qortal.repository.DataException;
import org.qortal.repository.Repository;
import org.qortal.repository.RepositoryManager;
import org.qortal.test.common.AccountUtils;
import org.qortal.test.common.BlockUtils;
import org.qortal.test.common.Common;
import org.qortal.test.common.TestAccount;
import org.qortal.utils.Amounts;

public class RewardTests extends Common {

	@Before
	public void beforeTest() throws DataException {
		Common.useDefaultSettings();
	}

	@After
	public void afterTest() throws DataException {
		Common.orphanCheck();
	}

	@Test
	public void testSimpleReward() throws DataException {
		try (final Repository repository = RepositoryManager.getRepository()) {
			Map<String, Map<Long, Long>> initialBalances = AccountUtils.getBalances(repository, Asset.QORT);

			Long blockReward = BlockUtils.getNextBlockReward(repository);

			BlockUtils.mintBlock(repository);

			long expectedBalance = initialBalances.get("alice").get(Asset.QORT) + blockReward;
			AccountUtils.assertBalance(repository, "alice", Asset.QORT, expectedBalance);
		}
	}

	@Test
	public void testRewards() throws DataException {
		List<RewardByHeight> rewardsByHeight = BlockChain.getInstance().getBlockRewardsByHeight();

		try (final Repository repository = RepositoryManager.getRepository()) {
			Map<String, Map<Long, Long>> initialBalances = AccountUtils.getBalances(repository, Asset.QORT);

			int rewardIndex = rewardsByHeight.size() - 1;

			RewardByHeight rewardInfo = rewardsByHeight.get(rewardIndex);
			Long expectedBalance = initialBalances.get("alice").get(Asset.QORT);

			for (int height = rewardInfo.height; height > 1; --height) {
				if (height < rewardInfo.height) {
					--rewardIndex;
					rewardInfo = rewardsByHeight.get(rewardIndex);
				}

				BlockUtils.mintBlock(repository);

				expectedBalance += rewardInfo.reward;
			}

			AccountUtils.assertBalance(repository, "alice", Asset.QORT, expectedBalance);
		}
	}

	@Test
	public void testRewardSharing() throws DataException {
		final int share = 12_80; // 12.80%

		try (final Repository repository = RepositoryManager.getRepository()) {
			byte[] rewardSharePrivateKey = AccountUtils.rewardShare(repository, "alice", "bob", share);
			PrivateKeyAccount rewardShareAccount = new PrivateKeyAccount(repository, rewardSharePrivateKey);

			Map<String, Map<Long, Long>> initialBalances = AccountUtils.getBalances(repository, Asset.QORT);
			Long blockReward = BlockUtils.getNextBlockReward(repository);

			BlockMinter.mintTestingBlock(repository, rewardShareAccount);

			// We're expecting reward * 12.8% to Bob, the rest to Alice

			long bobShare = (blockReward * share) / 100L / 100L;
			AccountUtils.assertBalance(repository, "bob", Asset.QORT, initialBalances.get("bob").get(Asset.QORT) + bobShare);

			long aliceShare = blockReward - bobShare;
			AccountUtils.assertBalance(repository, "alice", Asset.QORT, initialBalances.get("alice").get(Asset.QORT) + aliceShare);
		}
	}


	@Test
	public void testLegacyQoraReward() throws DataException {
		Common.useSettings("test-settings-v2-qora-holder-extremes.json");

		long qoraHoldersShare = BlockChain.getInstance().getQoraHoldersShare();
		BigInteger qoraHoldersShareBI = BigInteger.valueOf(qoraHoldersShare);

		long qoraPerQort = BlockChain.getInstance().getQoraPerQortReward();
		BigInteger qoraPerQortBI = BigInteger.valueOf(qoraPerQort);

		try (final Repository repository = RepositoryManager.getRepository()) {
			Map<String, Map<Long, Long>> initialBalances = AccountUtils.getBalances(repository, Asset.QORT, Asset.LEGACY_QORA, Asset.QORT_FROM_QORA);

			Long blockReward = BlockUtils.getNextBlockReward(repository);
			BigInteger blockRewardBI = BigInteger.valueOf(blockReward);

			// Fetch all legacy QORA holder balances
			List<AccountBalanceData> qoraHolders = repository.getAccountRepository().getAssetBalances(Asset.LEGACY_QORA, true);
			long totalQoraHeld = 0L;
			for (AccountBalanceData accountBalanceData : qoraHolders)
				totalQoraHeld += accountBalanceData.getBalance();
			BigInteger totalQoraHeldBI = BigInteger.valueOf(totalQoraHeld);

			BlockUtils.mintBlock(repository);

			/*
			 * Example:
			 * 
			 * Block reward is 100 QORT, QORA-holders' share is 0.20 (20%) = 20 QORT
			 * 
			 * We hold 100 QORA
			 * Someone else holds 28 QORA
			 * Total QORA held: 128 QORA
			 * 
			 * Our portion of that is 100 QORA / 128 QORA * 20 QORT = 15.625 QORT
			 * 
			 * QORA holders earn at most 1 QORT per 250 QORA held.
			 * 
			 * So we can earn at most 100 QORA / 250 QORAperQORT = 0.4 QORT
			 * 
			 * Thus our block earning should be capped to 0.4 QORT.
			 */

			// Expected reward
			long qoraHoldersReward = blockRewardBI.multiply(qoraHoldersShareBI).divide(Amounts.MULTIPLIER_BI).longValue();
			assertTrue("QORA-holders share of block reward should be less than total block reward", qoraHoldersReward < blockReward);
			assertFalse("QORA-holders share of block reward should not be negative!", qoraHoldersReward < 0);
			BigInteger qoraHoldersRewardBI = BigInteger.valueOf(qoraHoldersReward);

			long ourQoraHeld = initialBalances.get("chloe").get(Asset.LEGACY_QORA);
			BigInteger ourQoraHeldBI = BigInteger.valueOf(ourQoraHeld);
			long ourQoraReward = qoraHoldersRewardBI.multiply(ourQoraHeldBI).divide(totalQoraHeldBI).longValue();
			assertTrue("Our QORA-related reward should be less than total QORA-holders share of block reward", ourQoraReward < qoraHoldersReward);
			assertFalse("Our QORA-related reward should not be negative!", ourQoraReward < 0);

			long ourQortFromQoraCap = Amounts.scaledDivide(ourQoraHeldBI, qoraPerQortBI);
			assertTrue("Our QORT-from-QORA cap should be greater than zero", ourQortFromQoraCap > 0);

			long expectedReward = Math.min(ourQoraReward, ourQortFromQoraCap);
			AccountUtils.assertBalance(repository, "chloe", Asset.QORT, initialBalances.get("chloe").get(Asset.QORT) + expectedReward);

			AccountUtils.assertBalance(repository, "chloe", Asset.QORT_FROM_QORA, initialBalances.get("chloe").get(Asset.QORT_FROM_QORA) + expectedReward);
		}
	}

	@Test
	public void testMaxLegacyQoraReward() throws DataException {
		Common.useSettings("test-settings-v2-qora-holder.json");

		long qoraPerQort = BlockChain.getInstance().getQoraPerQortReward();

		try (final Repository repository = RepositoryManager.getRepository()) {
			Map<String, Map<Long, Long>> initialBalances = AccountUtils.getBalances(repository, Asset.QORT, Asset.LEGACY_QORA, Asset.QORT_FROM_QORA);

			// Mint lots of blocks
			for (int i = 0; i < 100; ++i)
				BlockUtils.mintBlock(repository);

			// Expected balances to be limited by Dilbert's legacy QORA amount
			long expectedBalance = Amounts.scaledDivide(initialBalances.get("dilbert").get(Asset.LEGACY_QORA), qoraPerQort);
			AccountUtils.assertBalance(repository, "dilbert", Asset.QORT, initialBalances.get("dilbert").get(Asset.QORT) + expectedBalance);
			AccountUtils.assertBalance(repository, "dilbert", Asset.QORT_FROM_QORA, initialBalances.get("dilbert").get(Asset.QORT_FROM_QORA) + expectedBalance);
		}
	}

	/** Use Alice-Chloe reward-share to bump Chloe from level 0 to level 1, then check orphaning works as expected. */
	@Test
	public void testLevel1() throws DataException {
		List<Integer> cumulativeBlocksByLevel = BlockChain.getInstance().getCumulativeBlocksByLevel();

		try (final Repository repository = RepositoryManager.getRepository()) {
			TestAccount chloe = Common.getTestAccount(repository, "chloe");

			assertEquals(0, (int) chloe.getLevel());

			// Alice needs to mint block containing REWARD_SHARE BEFORE Alice loses minting privs
			byte[] aliceChloeRewardSharePrivateKey = AccountUtils.rewardShare(repository, "alice", "chloe", 0); // Block minted by Alice
			PrivateKeyAccount aliceChloeRewardShareAccount = new PrivateKeyAccount(repository, aliceChloeRewardSharePrivateKey);

			final int minterBlocksNeeded = cumulativeBlocksByLevel.get(1);
			// Mint enough blocks to bump testAccount level
			for (int bc = 0; bc < minterBlocksNeeded; ++bc)
				BlockMinter.mintTestingBlock(repository, aliceChloeRewardShareAccount);

			assertEquals(1, (int) chloe.getLevel());

			// Orphan back to genesis block
			BlockUtils.orphanToBlock(repository, 1);

			assertEquals(0, (int) chloe.getLevel());
		}
	}

	/** Test rewards to founders, one in reward-share, the other is self-share. */
	@Test
	public void testFounderRewards() throws DataException {
		Common.useSettings("test-settings-v2-founder-rewards.json");

		try (final Repository repository = RepositoryManager.getRepository()) {
			Long blockReward = BlockUtils.getNextBlockReward(repository);

			List<PrivateKeyAccount> mintingAndOnlineAccounts = new ArrayList<>();

			// Alice to mint, therefore online
			PrivateKeyAccount aliceSelfShare = Common.getTestAccount(repository, "alice-reward-share");
			mintingAndOnlineAccounts.add(aliceSelfShare);

			// Bob self-share NOT online

			// Chloe self-share and reward-share with Dilbert both online
			PrivateKeyAccount chloeSelfShare = Common.getTestAccount(repository, "chloe-reward-share");
			mintingAndOnlineAccounts.add(chloeSelfShare);

			PrivateKeyAccount chloeDilbertRewardShare = new PrivateKeyAccount(repository, Base58.decode("HuiyqLipUN1V9p1HZfLhyEwmEA6BTaT2qEfjgkwPViV4"));
			mintingAndOnlineAccounts.add(chloeDilbertRewardShare);

			BlockMinter.mintTestingBlock(repository, mintingAndOnlineAccounts.toArray(new PrivateKeyAccount[0]));

			// 2 founders online so blockReward divided by 2
			int founderCount = 2;
			long perFounderReward = blockReward / founderCount;

			// Alice simple self-share so her reward is perFounderReward
			AccountUtils.assertBalance(repository, "alice", Asset.QORT, perFounderReward);

			// Bob not online so his reward is zero
			AccountUtils.assertBalance(repository, "bob", Asset.QORT, 0L);

			// Chloe has two reward-shares, so her reward is divided by 2
			int chloeSharesCount = 2;
			long chloePerShareReward = perFounderReward / chloeSharesCount;

			// Her self-share gets chloePerShareReward
			long chloeExpectedBalance = chloePerShareReward;

			// Her reward-share with Dilbert: 25% goes to Dilbert
			int dilbertSharePercent = 25;
			long dilbertExpectedBalance = (chloePerShareReward * dilbertSharePercent) / 100L;

			// The remaining 75% goes to Chloe
			long rewardShareRemaining = chloePerShareReward - dilbertExpectedBalance;
			chloeExpectedBalance += rewardShareRemaining;
			AccountUtils.assertBalance(repository, "chloe", Asset.QORT, chloeExpectedBalance);
		}
	}

	/** Check account-level-based reward scaling when no founders are online. */
	@Test
	public void testNoFounderRewardScaling() throws DataException {
		Common.useSettings("test-settings-v2-reward-scaling.json");

		try (final Repository repository = RepositoryManager.getRepository()) {
			// Dilbert needs to create a self-share
			byte[] dilbertSelfSharePrivateKey = AccountUtils.rewardShare(repository, "dilbert", "dilbert", 0); // Block minted by Alice
			PrivateKeyAccount dilbertSelfShareAccount = new PrivateKeyAccount(repository, dilbertSelfSharePrivateKey);

			Map<String, Map<Long, Long>> initialBalances = AccountUtils.getBalances(repository, Asset.QORT, Asset.LEGACY_QORA, Asset.QORT_FROM_QORA);

			long blockReward = BlockUtils.getNextBlockReward(repository);

			BlockMinter.mintTestingBlock(repository, dilbertSelfShareAccount);

			/*
			 * Dilbert is only account 'online'.
			 * No founders online.
			 * Some legacy QORA holders.
			 * 
			 * So Dilbert should receive 100% - legacy QORA holder's share.
			 */

			final long qoraHoldersShare = BlockChain.getInstance().getQoraHoldersShare();
			final long remainingShare = 1_00000000 - qoraHoldersShare;

			long dilbertExpectedBalance = initialBalances.get("dilbert").get(Asset.QORT);
			dilbertExpectedBalance += Amounts.roundDownScaledMultiply(blockReward, remainingShare);

			AccountUtils.assertBalance(repository, "dilbert", Asset.QORT, dilbertExpectedBalance);

			// After several blocks, the legacy QORA holder should be maxxed out
			for (int i = 0; i < 10; ++i)
				BlockUtils.mintBlock(repository);

			// Now Dilbert should be receiving 100% of block reward
			blockReward = BlockUtils.getNextBlockReward(repository);

			BlockMinter.mintTestingBlock(repository, dilbertSelfShareAccount);

			AccountUtils.assertBalance(repository, "dilbert", Asset.QORT, dilbertExpectedBalance + blockReward);
		}
	}

	/** Check leftover legacy QORA reward goes to online founders. */
	@Test
	public void testLeftoverReward() throws DataException {
		Common.useSettings("test-settings-v2-leftover-reward.json");

		try (final Repository repository = RepositoryManager.getRepository()) {
			Map<String, Map<Long, Long>> initialBalances = AccountUtils.getBalances(repository, Asset.QORT, Asset.LEGACY_QORA, Asset.QORT_FROM_QORA);

			long blockReward = BlockUtils.getNextBlockReward(repository);

			BlockUtils.mintBlock(repository); // Block minted by Alice self-share

			// Chloe maxxes out her legacy QORA reward so some is leftover to reward to Alice.

			TestAccount chloe = Common.getTestAccount(repository, "chloe");
			final long chloeQortFromQora = chloe.getConfirmedBalance(Asset.QORT_FROM_QORA);

			long expectedBalance = initialBalances.get("alice").get(Asset.QORT) + blockReward - chloeQortFromQora;
			AccountUtils.assertBalance(repository, "alice", Asset.QORT, expectedBalance);
		}
	}

}
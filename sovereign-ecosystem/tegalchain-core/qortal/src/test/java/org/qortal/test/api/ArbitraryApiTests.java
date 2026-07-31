package org.qortal.test.api;

import static org.junit.Assert.*;

import org.junit.Before;
import org.junit.Test;
import org.qortal.api.resource.ArbitraryResource;
import org.qortal.api.resource.TransactionsResource.ConfirmationStatus;
import org.qortal.test.common.ApiCommon;

public class ArbitraryApiTests extends ApiCommon {

	private ArbitraryResource arbitraryResource;

	@Before
	public void buildResource() {
		this.arbitraryResource = (ArbitraryResource) ApiCommon.buildResource(ArbitraryResource.class);
	}

	@Test
	public void testSearch() {
		Integer[] startingBlocks = new Integer[] { null, 0, 1, 999999999 };
		Integer[] blockLimits = new Integer[] { null, 0, 1, 999999999 };
		Integer[] txGroupIds = new Integer[] { null, 0, 1, 999999999 };
		Integer[] services = new Integer[] { null, 0, 1, 999999999 };
		String[] addresses = new String[] { null, this.aliceAddress };
		ConfirmationStatus[] confirmationStatuses = new ConfirmationStatus[] { ConfirmationStatus.UNCONFIRMED, ConfirmationStatus.CONFIRMED, ConfirmationStatus.BOTH };

		for (Integer startBlock : startingBlocks)
			for (Integer blockLimit : blockLimits)
				for (Integer txGroupId : txGroupIds)
					for (Integer service : services)
						for (String address : addresses)
							for (ConfirmationStatus confirmationStatus : confirmationStatuses) {
								if (confirmationStatus != ConfirmationStatus.CONFIRMED && (startBlock != null || blockLimit != null))
									continue;

								assertNotNull(this.arbitraryResource.searchTransactions(startBlock, blockLimit, txGroupId, service, address, confirmationStatus, 20, null, null));
								assertNotNull(this.arbitraryResource.searchTransactions(startBlock, blockLimit, txGroupId, service, address, confirmationStatus, 1, 1, true));
							}
	}

}

package org.qortal.repository;

import java.util.List;

import org.qortal.data.chat.ActiveChats;
import org.qortal.data.chat.ChatMessage;
import org.qortal.data.transaction.ChatTransactionData;

public interface ChatRepository {

	/**
	 * Returns CHAT messages matching criteria.
	 * <p>
	 * Expects EITHER non-null txGroupID OR non-null sender and recipient addresses.
	 */
	public List<ChatMessage> getMessagesMatchingCriteria(Long before, Long after,
			Integer txGroupId, List<String> involving,
			Integer limit, Integer offset, Boolean reverse) throws DataException;

	public ChatMessage toChatMessage(ChatTransactionData chatTransactionData) throws DataException;

	public ActiveChats getActiveChats(String address) throws DataException;

}

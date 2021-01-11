package org.qortal.repository;

import java.util.List;

import org.qortal.data.network.PeerData;
import org.qortal.network.PeerAddress;

public interface NetworkRepository {

	public List<PeerData> getAllPeers() throws DataException;

	public void save(PeerData peerData) throws DataException;

	public int delete(PeerAddress peerAddress) throws DataException;

	public int deleteAllPeers() throws DataException;

}

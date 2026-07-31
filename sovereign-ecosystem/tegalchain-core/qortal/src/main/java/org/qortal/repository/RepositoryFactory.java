package org.qortal.repository;

public interface RepositoryFactory {

	public boolean wasPristineAtOpen();

	public RepositoryFactory reopen() throws DataException;

	public Repository getRepository() throws DataException;

	public Repository tryRepository() throws DataException;

	public void close() throws DataException;

}

package org.qortal.at;

import org.ciyam.at.AtLogger;

public class QortalAtLoggerFactory implements org.ciyam.at.AtLoggerFactory {

	private static QortalAtLoggerFactory instance;

	private QortalAtLoggerFactory() {
	}

	public static synchronized QortalAtLoggerFactory getInstance() {
		if (instance == null)
			instance = new QortalAtLoggerFactory();

		return instance;
	}

	@Override
	public AtLogger create(final Class<?> loggerName) {
		return QortalAtLogger.create(loggerName);
	}

}

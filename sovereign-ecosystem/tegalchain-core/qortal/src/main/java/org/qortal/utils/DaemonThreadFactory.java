package org.qortal.utils;

import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.atomic.AtomicInteger;

public class DaemonThreadFactory implements ThreadFactory {

	private final String name;
	private final AtomicInteger threadNumber = new AtomicInteger(1);

	public DaemonThreadFactory(String name) {
		this.name = name;
	}

	public DaemonThreadFactory() {
		this(null);
	}

	@Override
	public Thread newThread(Runnable runnable) {
		Thread thread = Executors.defaultThreadFactory().newThread(runnable);
		thread.setDaemon(true);

		if (this.name != null)
			thread.setName(this.name + "-" + this.threadNumber.getAndIncrement());

		return thread;
	}

}

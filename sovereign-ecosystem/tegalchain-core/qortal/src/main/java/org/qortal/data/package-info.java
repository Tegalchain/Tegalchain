// Only edit org/qortal/data/package-info.java
// Other package-info.java files are generated using above file

@XmlJavaTypeAdapters({
	@XmlJavaTypeAdapter(
		type = byte[].class,
		value = org.qortal.api.Base58TypeAdapter.class
	), @XmlJavaTypeAdapter(
		type = java.math.BigDecimal.class,
		value = org.qortal.api.BigDecimalTypeAdapter.class
	)
})
package org.qortal.data;

import javax.xml.bind.annotation.adapters.XmlJavaTypeAdapter;
import javax.xml.bind.annotation.adapters.XmlJavaTypeAdapters;

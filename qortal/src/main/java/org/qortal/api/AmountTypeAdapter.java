package org.qortal.api;

import java.math.BigDecimal;

import javax.xml.bind.annotation.adapters.XmlAdapter;

import org.qortal.utils.Amounts;

public class AmountTypeAdapter extends XmlAdapter<String, Long> {

	@Override
	public Long unmarshal(String input) throws Exception {
		if (input == null)
			return null;

		return new BigDecimal(input).setScale(8).unscaledValue().longValue();
	}

	@Override
	public String marshal(Long output) throws Exception {
		if (output == null)
			return null;

		return Amounts.prettyAmount(output);
	}

}

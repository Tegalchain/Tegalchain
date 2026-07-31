package org.qortal.data.account;


import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.adapters.XmlJavaTypeAdapter;

// All properties to be converted to JSON via JAXB
@XmlAccessorType(XmlAccessType.FIELD)
public class QortFromQoraData {

	// Properties

	private String address;

	// Not always present
	@XmlJavaTypeAdapter(value = org.qortal.api.AmountTypeAdapter.class)
	private Long finalQortFromQora;

	// Not always present
	private Integer finalBlockHeight;

	// Constructors

	// necessary for JAXB
	protected QortFromQoraData() {
	}

	public QortFromQoraData(String address, Long finalQortFromQora, Integer finalBlockHeight) {
		this.address = address;
		this.finalQortFromQora = finalQortFromQora;
		this.finalBlockHeight = finalBlockHeight;
	}

	// Getters/Setters

	public String getAddress() {
		return this.address;
	}

	public Long getFinalQortFromQora() {
		return this.finalQortFromQora;
	}

	public void setFinalQortFromQora(Long finalQortFromQora) {
		this.finalQortFromQora = finalQortFromQora;
	}

	public Integer getFinalBlockHeight() {
		return this.finalBlockHeight;
	}

	public void setFinalBlockHeight(Integer finalBlockHeight) {
		this.finalBlockHeight = finalBlockHeight;
	}

}

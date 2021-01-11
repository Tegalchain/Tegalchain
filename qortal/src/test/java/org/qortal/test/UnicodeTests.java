package org.qortal.test;

import static org.junit.Assert.*;
import static org.qortal.utils.Unicode.*;

import org.junit.Test;
import org.qortal.utils.Unicode;

public class UnicodeTests {

	@Test
	public void testWhitespace() {
		String input = "  " + NO_BREAK_SPACE + "test  ";

		String output = Unicode.normalize(input);

		assertEquals("trim & collapse failed", "test", output);
	}

	@Test
	public void testCaseComparison() {
		String input1 = "  " + NO_BREAK_SPACE + "test  ";
		String input2 = "  " + NO_BREAK_SPACE + "TEST  " + ZERO_WIDTH_SPACE;

		assertEquals("strings should match", Unicode.sanitize(input1), Unicode.sanitize(input2));
	}

	@Test
	public void testHomoglyph() {
		String omicron = "\u03bf";

		String input1 = "  " + NO_BREAK_SPACE + "toÁst  ";
		String input2 = "  " + NO_BREAK_SPACE + "t" + omicron + "ast  " + ZERO_WIDTH_SPACE;

		assertEquals("strings should match", Unicode.sanitize(input1), Unicode.sanitize(input2));
	}

}

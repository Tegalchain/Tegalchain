#ifndef NO_STDINT_TYPEDEFS
	typedef unsigned char uint8_t;
	typedef unsigned int uint32_t;
	typedef unsigned long long uint64_t;
#endif

#define INTEGER_MAX_VALUE 0x7fffffffULL

uint64_t xoshiro256p(uint64_t state[]) {
	uint64_t result = state[0] + state[3];
	uint64_t temp = state[1] << 17;

	state[2] ^= state[0];
	state[3] ^= state[1];
	state[1] ^= state[2];
	state[0] ^= state[3];

	state[2] ^= temp;
	state[3] = (state[3] << 45) | (state[3] >> (64 - 45)); // rol64(s[3], 45);

	return result;
}

int numberOfLeadingZeros32(uint32_t i) {
	if (i <= 0)
		return i == 0 ? 32 : 0;
	int n = 31;
	if (i >= 1 << 16) { n -= 16; i >>= 16; }
	if (i >= 1 <<  8) { n -=  8; i >>=  8; }
	if (i >= 1 <<  4) { n -=  4; i >>=  4; }
	if (i >= 1 <<  2) { n -=  2; i >>=  2; }
	return n - (i >> 1);
}

int numberOfLeadingZeros64(uint64_t i) {
	uint32_t x = (uint32_t) (i >> 32);
	return x == 0
			? 32 + numberOfLeadingZeros32((uint32_t) i)
			: numberOfLeadingZeros32(x);
}

uint32_t compute2(uint8_t *hash, uint64_t *workBuffer, uint32_t workBufferLength, int difficulty) {
	uint64_t longHash[4];
	for (int l = 0; l < 4; ++l) {
		longHash[l] = 0;

		for (int b = 0; b < 8; ++b) {
			longHash[l] = longHash[l] << 8 | hash[l * 8 + b];
		}
	}

	uint32_t longBufferLength = workBufferLength / 8;

	uint64_t state[4] = { 0, 0, 0, 0 };

	uint64_t seed = 8682522807148012ULL;
	uint64_t seedMultiplier = 1181783497276652981ULL;

	// For each nonce...
	uint32_t nonce = -1;
	uint64_t result = 0;
	do {
		++nonce;

		seed *= seedMultiplier; // per nonce

		state[0] = longHash[0] ^ seed;
		state[1] = longHash[1] ^ seed;
		state[2] = longHash[2] ^ seed;
		state[3] = longHash[3] ^ seed;

		// Fill work buffer with random
		for (uint32_t i = 0; i < longBufferLength; ++i)
			workBuffer[i] = xoshiro256p(state);

		// Random bounce through whole buffer
		result = workBuffer[0];
		for (uint32_t i = 0; i < 1024; ++i) {
			uint32_t index = (uint32_t) (xoshiro256p(state) & INTEGER_MAX_VALUE) % longBufferLength;
			result ^= workBuffer[index];
		}

		// Return if final value > difficulty
	} while (numberOfLeadingZeros64(result) < difficulty);

	return nonce;
}

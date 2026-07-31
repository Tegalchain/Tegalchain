typedef unsigned char uint8_t;
typedef unsigned int uint32_t;
typedef unsigned long long uint64_t;

uint32_t test() {
	return 4013;
}

uint32_t test2(uint8_t values[], int count) {
	uint32_t sum = 0;

	for (int i = 0; i < count; ++i)
		sum += values[i];

	return sum;
}

void test3(uint8_t hash[], uint64_t longHash[]) {
	for (int l = 0; l < 4; ++l) {
		longHash[l] = 0;

		for (int b = 0; b < 8; ++b)
			longHash[l] = longHash[l] << 8 | hash[l * 8 + b];
	}
}

void test4(uint64_t *result) {
	uint64_t seed = 8682522807148012ULL;
	uint64_t seedMultiplier = 1181783497276652981ULL;

	*result = seed * seedMultiplier;
}

void test5(uint64_t longHash[], uint64_t state[]) {
	uint64_t seed = 8682522807148012ULL;
	uint64_t seedMultiplier = 1181783497276652981ULL;

	seed *= seedMultiplier; // per nonce

	state[0] = longHash[0] ^ seed;
	state[1] = longHash[1] ^ seed;
	state[2] = longHash[2] ^ seed;
	state[3] = longHash[3] ^ seed;
}

uint32_t shr(uint32_t in, int shift) {
	return in >> shift;
}

void xoshiro256p(uint64_t state[], uint64_t *result) {
	*result = state[0] + state[3];
	uint64_t temp = state[1] << 17;

	state[2] ^= state[0];
	state[3] ^= state[1];
	state[1] ^= state[2];
	state[0] ^= state[3];

	state[2] ^= temp;
	state[3] = (state[3] << 45) | (state[3] >> (64 - 45)); // rol64(s[3], 45);
}

void fillWorkBuffer(uint64_t workBuffer[], int workBufferLength, uint64_t state[]) {
	// Fill work buffer with random
	for (uint32_t i = 0; i < workBufferLength; ++i)
		xoshiro256p(state, &workBuffer[i]);
}

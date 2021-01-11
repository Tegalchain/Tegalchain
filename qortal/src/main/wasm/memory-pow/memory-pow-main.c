#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include <openssl/evp.h>

#define NO_STDINT_TYPEDEFS
#include "memory-pow.c"

	unsigned int toInt(char c) {
		if (c >= '0' && c <= '9') return      c - '0';
		if (c >= 'A' && c <= 'F') return 10 + c - 'A';
		if (c >= 'a' && c <= 'f') return 10 + c - 'a';
		return -1;
	}

	void hexToRaw(char *hex, uint8_t *data, int dataLength) {
		for (int i = 0; i < dataLength; ++i) {
			data[i] = 16 * toInt(hex[i * 2]) + toInt(hex[i * 2 + 1]);
		}
	}

	void digest(uint8_t *message, int messageLength, uint8_t *hash) {
		EVP_MD_CTX *mdctx = EVP_MD_CTX_new();
		const EVP_MD *md = EVP_sha256();

		EVP_DigestInit_ex(mdctx, md, NULL);
		EVP_DigestUpdate(mdctx, message, messageLength);
		EVP_DigestFinal_ex(mdctx, hash, NULL);
	}

	int main(int argc, char *argv[], char *env[]) {
		if (argc < 2) {
			fprintf(stderr, "usage: %s hex [difficulty]\n", argv[0]);
			return 2;
		}

		int dataLength = strlen(argv[1]) / 2;
		uint8_t data[dataLength];
		hexToRaw(argv[1], data, dataLength);

		int difficulty = 12;
		if (argc > 2)
			sscanf(argv[2], "%d", &difficulty);

		printf("Using difficulty: %d\n", difficulty);

		// Hash data with SHA256
		uint8_t hash[32];
		digest(data, dataLength, hash);

		size_t workBufferLength = 8 * 1024 * 1024;
		uint64_t *workBuffer = (uint64_t *) malloc(workBufferLength);

		uint32_t nonce = compute2(hash, workBuffer, workBufferLength, difficulty);

		printf("nonce: %d\n", nonce);
	}

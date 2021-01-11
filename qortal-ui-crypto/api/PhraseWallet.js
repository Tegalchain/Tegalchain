/*
Copyright 2017-2018 @ irontiga and vbcs (original developer)
*/
'use strict';
import Base58 from './deps/Base58.js'
import { Sha256, Sha512 } from 'asmcrypto.js'
import nacl from './deps/nacl-fast.js'
import utils from './deps/utils.js'

import BitcoinHDWallet from './bitcoin/BitcoinHDWallet.js';
import LitecoinHDWallet from './bitcoin/LitecoinHDWallet.js';

import { generateSaveWalletData } from './storeWallet.js'

import publicKeyToAddress from './wallet/publicKeyToAddress.js'

export default class PhraseWallet {
    constructor(seed, walletVersion) {

        this._walletVersion = walletVersion || 2
        this.seed = seed

        this.savedSeedData = {}
        this.hasBeenSaved = false
    }

    set seed(seed) {
        this._byteSeed = seed
        this._base58Seed = Base58.encode(seed)

        this._addresses = []

        this.genAddress(0)
    }

    getAddress(nonce) {
        return this._addresses[nonce]
    }

    get addresses() {
        return this._addresses
    }

    get addressIDs() {
        return this._addresses.map(addr => {
            return addr.address
        })
    }

    get seed() {
        return this._byteSeed
    }

    addressExists(nonce) {
        return this._addresses[nonce] != undefined
    }

    _genAddressSeed(seed) {
        let newSeed = new Sha512().process(seed).finish().result
        newSeed = new Sha512().process(utils.appendBuffer(newSeed, seed)).finish().result
        return newSeed
    }

    genAddress(nonce) {
        if (nonce >= this._addresses.length) {
            this._addresses.length = nonce + 1
        }

        if (this.addressExists(nonce)) {
            return this.addresses[nonce]
        }

        const nonceBytes = utils.int32ToBytes(nonce)

        let addrSeed = new Uint8Array()
        addrSeed = utils.appendBuffer(addrSeed, nonceBytes)
        addrSeed = utils.appendBuffer(addrSeed, this._byteSeed)
        addrSeed = utils.appendBuffer(addrSeed, nonceBytes)

        if (this._walletVersion == 1) {
            addrSeed = new Sha256().process(
                new Sha256()
                    .process(addrSeed)
                    .finish()
                    .result
            ).finish().result

            addrSeed = this._byteSeed
        } else {
            addrSeed = this._genAddressSeed(addrSeed).slice(0, 32)
        }

        const addrKeyPair = nacl.sign.keyPair.fromSeed(new Uint8Array(addrSeed));

        const address = publicKeyToAddress(addrKeyPair.publicKey);
        const qoraAddress = publicKeyToAddress(addrKeyPair.publicKey, true);

        // Create Bitcoin HD Wallet 
        const btcSeed = [...addrSeed];
        const btcWallet = new BitcoinHDWallet().createWallet(new Uint8Array(btcSeed));

        // Create Litecoin HD Wallet 
        const ltcSeed = [...addrSeed];
        const ltcWallet = new LitecoinHDWallet().createWallet(new Uint8Array(ltcSeed));

        this._addresses[nonce] = {
            address,
            btcWallet,
            ltcWallet,
            qoraAddress,
            keyPair: {
                publicKey: addrKeyPair.publicKey,
                privateKey: addrKeyPair.secretKey
            },
            base58PublicKey: Base58.encode(addrKeyPair.publicKey),
            seed: addrSeed,
            nonce: nonce
        }
        return this._addresses[nonce]
    }

    generateSaveWalletData(...args) {
        return generateSaveWalletData(this, ...args)
    }
}

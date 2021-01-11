const user = require('./default.config.js').user
module.exports = {
	node: 1, // set to mainnet
	server: {
		primary: {
			port: 12388,
			address: '0.0.0.0',
		},
	},
}

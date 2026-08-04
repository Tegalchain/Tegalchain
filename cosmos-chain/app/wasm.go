package app

import (
	"fmt"
	"path/filepath"

	storetypes "cosmossdk.io/store/types"
	"github.com/CosmWasm/wasmd/x/wasm"
	wasmkeeper "github.com/CosmWasm/wasmd/x/wasm/keeper"
	wasmtypes "github.com/CosmWasm/wasmd/x/wasm/types"
	"github.com/cosmos/cosmos-sdk/client/flags"
	"github.com/cosmos/cosmos-sdk/runtime"
	servertypes "github.com/cosmos/cosmos-sdk/server/types"
	authtypes "github.com/cosmos/cosmos-sdk/x/auth/types"
	distrkeeper "github.com/cosmos/cosmos-sdk/x/distribution/keeper"
	"github.com/spf13/cast"
)

// registerWasmModules wires x/wasm without IBC.
//
// Track B gretelemetry stays on depinject. wasmd has no ProvideModule for SDK 0.53,
// so we RegisterStores/RegisterModules after appBuilder.Build.
// IBC keepers are nil: lab store/instantiate/execute for tx-tel does not need IBC.
// Full IBC + ignite wasm app remains a follow-up (see COSMWASM-ENABLEMENT.md).
func (app *App) registerWasmModules(appOpts servertypes.AppOptions) error {
	if err := app.RegisterStores(
		storetypes.NewKVStoreKey(wasmtypes.StoreKey),
	); err != nil {
		return fmt.Errorf("register wasm store: %w", err)
	}

	nodeConfig, err := wasm.ReadNodeConfig(appOpts)
	if err != nil {
		return fmt.Errorf("read wasm node config: %w", err)
	}

	homePath := cast.ToString(appOpts.Get(flags.FlagHome))
	if homePath == "" {
		homePath = DefaultNodeHome
	}
	wasmDir := filepath.Join(homePath, "wasm")

	// Authority: module address derived from "gov" (gov module not scaffolded yet).
	authority := authtypes.NewModuleAddress("gov").String()

	app.WasmKeeper = wasmkeeper.NewKeeper(
		app.AppCodec(),
		runtime.NewKVStoreService(app.GetKey(wasmtypes.StoreKey)),
		app.AuthKeeper,
		app.BankKeeper,
		app.StakingKeeper,
		distrkeeper.NewQuerier(app.DistrKeeper),
		nil, // ICS4Wrapper — no IBC
		nil, // ChannelKeeper — no IBC
		nil, // ChannelKeeperV2 — no IBC
		nil, // ICS20TransferPortSource — no IBC
		app.MsgServiceRouter(),
		app.GRPCQueryRouter(),
		wasmDir,
		nodeConfig,
		wasmtypes.VMConfig{},
		wasmkeeper.BuiltInCapabilities(),
		authority,
	)

	if err := app.RegisterModules(
		wasm.NewAppModule(
			app.AppCodec(),
			&app.WasmKeeper,
			app.StakingKeeper,
			app.AuthKeeper,
			app.BankKeeper,
			app.MsgServiceRouter(),
			nil, // no legacy x/params subspace
		),
	); err != nil {
		return fmt.Errorf("register wasm module: %w", err)
	}

	return nil
}

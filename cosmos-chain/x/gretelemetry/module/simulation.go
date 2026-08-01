package gretelemetry

import (
	"cosmossdk.io/core/address"
	sdk "github.com/cosmos/cosmos-sdk/types"
	"github.com/cosmos/cosmos-sdk/types/module"
	simtypes "github.com/cosmos/cosmos-sdk/types/simulation"
	"math/rand"

	gretelemetrysimulation "github.com/Tegalchain/Tegalchain/chain/x/gretelemetry/simulation"
	"github.com/Tegalchain/Tegalchain/chain/x/gretelemetry/types"
)

// GenerateGenesisState creates a randomized GenState of the module.
func (AppModule) GenerateGenesisState(simState *module.SimulationState) {
	accs := make([]string, len(simState.Accounts))
	for i, acc := range simState.Accounts {
		accs[i] = acc.Address.String()
	}
	gretelemetryGenesis := types.GenesisState{
		Params: types.DefaultParams(),
	}
	simState.GenState[types.ModuleName] = simState.Cdc.MustMarshalJSON(&gretelemetryGenesis)
}

// RegisterStoreDecoder registers a decoder.
func (am AppModule) RegisterStoreDecoder(_ simtypes.StoreDecoderRegistry) {}

// WeightedOperations returns the all the gov module operations with their respective weights.
func (am AppModule) WeightedOperations(simState module.SimulationState) []simtypes.WeightedOperation {
	operations := make([]simtypes.WeightedOperation, 0)
	const (
		opWeightMsgAnchorTelemetry          = "op_weight_msg_gretelemetry"
		defaultWeightMsgAnchorTelemetry int = 100
	)

	var weightMsgAnchorTelemetry int
	simState.AppParams.GetOrGenerate(opWeightMsgAnchorTelemetry, &weightMsgAnchorTelemetry, nil,
		func(_ *rand.Rand) {
			weightMsgAnchorTelemetry = defaultWeightMsgAnchorTelemetry
		},
	)
	operations = append(operations, simulation.NewWeightedOperation(
		weightMsgAnchorTelemetry,
		gretelemetrysimulation.SimulateMsgAnchorTelemetry(am.authKeeper, am.bankKeeper, am.keeper, simState.TxConfig),
	))

	return operations
}

// ProposalMsgs returns msgs used for governance proposals for simulations.
func (am AppModule) ProposalMsgs(simState module.SimulationState) []simtypes.WeightedProposalMsg {
	return []simtypes.WeightedProposalMsg{}
}
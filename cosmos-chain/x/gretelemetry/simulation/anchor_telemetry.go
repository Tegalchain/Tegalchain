package simulation

import (
	"math/rand"

	"github.com/cosmos/cosmos-sdk/baseapp"
	sdk "github.com/cosmos/cosmos-sdk/types"
	simtypes "github.com/cosmos/cosmos-sdk/types/simulation"

	"github.com/Tegalchain/Tegalchain/chain/x/gretelemetry/keeper"
	"github.com/Tegalchain/Tegalchain/chain/x/gretelemetry/types"
)

func SimulateMsgAnchorTelemetry(
	ak types.AuthKeeper,
	bk types.BankKeeper,
	k keeper.Keeper,
	txGen client.TxConfig,
) simtypes.Operation {
	return func(r *rand.Rand, app *baseapp.BaseApp, ctx sdk.Context, accs []simtypes.Account, chainID string,
	) (simtypes.OperationMsg, []simtypes.FutureOperation, error) {
		simAccount, _ := simtypes.RandomAcc(r, accs)
		msg := &types.MsgAnchorTelemetry{
			Creator: simAccount.Address.String(),
		}

		// TODO: Handle the AnchorTelemetry simulation

		return simtypes.NoOpMsg(types.ModuleName, sdk.MsgTypeURL(msg), "AnchorTelemetry simulation not implemented"), nil, nil
	}
}

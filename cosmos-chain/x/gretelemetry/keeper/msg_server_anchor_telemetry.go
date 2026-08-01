package keeper

import (
	"context"

	errorsmod "cosmossdk.io/errors"

	"github.com/Tegalchain/Tegalchain/chain/x/gretelemetry/types"
)

func (k msgServer) AnchorTelemetry(ctx context.Context, msg *types.MsgAnchorTelemetry) (*types.MsgAnchorTelemetryResponse, error) {
	if _, err := k.addressCodec.StringToBytes(msg.Creator); err != nil {
		return nil, errorsmod.Wrap(err, "invalid creator address")
	}

	// TODO: persist GTR anchor (content_hash, attesters) — Phase 5 lab path is
	// POST /tegalchain/gretelemetry/v1/anchor; CosmJS/Tx maps to this Msg.

	return &types.MsgAnchorTelemetryResponse{
		GtrId: msg.GtrId,
	}, nil
}

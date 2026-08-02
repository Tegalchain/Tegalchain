package keeper

import (
	"context"
	"encoding/json"
	"fmt"

	errorsmod "cosmossdk.io/errors"
	sdkerrors "github.com/cosmos/cosmos-sdk/types/errors"

	"github.com/Tegalchain/Tegalchain/chain/x/gretelemetry/types"
)

// storedAnchor is the on-chain JSON record for a GTR summary (hash + metadata only).
type storedAnchor struct {
	GtrId              string   `json:"gtr_id"`
	ContentHash        string   `json:"content_hash"`
	AttesterIds        []string `json:"attester_ids"`
	MeasurementType    string   `json:"measurement_type"`
	Timestamp          string   `json:"timestamp"`
	AnchorTimestamp    string   `json:"anchor_timestamp,omitempty"`
	BlockCandidateHash string   `json:"block_candidate_hash,omitempty"`
	Creator            string   `json:"creator"`
}

func (k msgServer) AnchorTelemetry(ctx context.Context, msg *types.MsgAnchorTelemetry) (*types.MsgAnchorTelemetryResponse, error) {
	if _, err := k.addressCodec.StringToBytes(msg.Creator); err != nil {
		return nil, errorsmod.Wrap(err, "invalid creator address")
	}
	if msg.GtrId == "" {
		return nil, errorsmod.Wrap(sdkerrors.ErrInvalidRequest, "gtr_id required")
	}
	if msg.ContentHash == "" {
		return nil, errorsmod.Wrap(sdkerrors.ErrInvalidRequest, "content_hash required")
	}

	exists, err := k.Anchors.Has(ctx, msg.GtrId)
	if err != nil {
		return nil, err
	}
	if exists {
		return nil, errorsmod.Wrapf(sdkerrors.ErrInvalidRequest, "gtr_id already anchored: %s", msg.GtrId)
	}

	record := storedAnchor{
		GtrId:              msg.GtrId,
		ContentHash:        msg.ContentHash,
		AttesterIds:        msg.AttesterIds,
		MeasurementType:    msg.MeasurementType,
		Timestamp:          msg.Timestamp,
		AnchorTimestamp:    msg.AnchorTimestamp,
		BlockCandidateHash: msg.BlockCandidateHash,
		Creator:            msg.Creator,
	}
	raw, err := json.Marshal(record)
	if err != nil {
		return nil, fmt.Errorf("marshal anchor: %w", err)
	}
	if err := k.Anchors.Set(ctx, msg.GtrId, string(raw)); err != nil {
		return nil, err
	}

	// Txhash is filled by the broadcast layer (CLI/LCD), not the msg handler.
	return &types.MsgAnchorTelemetryResponse{
		GtrId: msg.GtrId,
	}, nil
}

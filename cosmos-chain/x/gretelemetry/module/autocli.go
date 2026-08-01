package gretelemetry

import (
	autocliv1 "cosmossdk.io/api/cosmos/autocli/v1"

	"github.com/Tegalchain/Tegalchain/chain/x/gretelemetry/types"
)

// AutoCLIOptions implements the autocli.HasAutoCLIConfig interface.
func (am AppModule) AutoCLIOptions() *autocliv1.ModuleOptions {
	return &autocliv1.ModuleOptions{
		Query: &autocliv1.ServiceCommandDescriptor{
			Service: types.Query_serviceDesc.ServiceName,
			RpcCommandOptions: []*autocliv1.RpcCommandOptions{
				{
					RpcMethod: "Params",
					Use:       "params",
					Short:     "Shows the parameters of the module",
				},
			},
		},
		Tx: &autocliv1.ServiceCommandDescriptor{
			Service:              types.Msg_serviceDesc.ServiceName,
			EnhanceCustomCommand: true, // only required if you want to use the custom command
			RpcCommandOptions: []*autocliv1.RpcCommandOptions{
				{
					RpcMethod: "UpdateParams",
					Skip:      true, // skipped because authority gated
				},
				{
					RpcMethod:      "AnchorTelemetry",
					Use:            "anchor-telemetry [gtr-id] [content-hash] [attester-ids] [measurement-type] [timestamp] [anchor-timestamp] [block-candidate-hash]",
					Short:          "Send a anchor-telemetry tx",
					PositionalArgs: []*autocliv1.PositionalArgDescriptor{{ProtoField: "gtr_id"}, {ProtoField: "content_hash"}, {ProtoField: "attester_ids"}, {ProtoField: "measurement_type"}, {ProtoField: "timestamp"}, {ProtoField: "anchor_timestamp"}, {ProtoField: "block_candidate_hash"}},
				},
			},
		},
	}
}

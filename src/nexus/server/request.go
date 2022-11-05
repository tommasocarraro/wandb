package server

import (
    //"context"
    "fmt"
    "github.com/wandb/wandb/nexus/service"
    log "github.com/sirupsen/logrus"
)

// import "wandb.ai/wandb/wbserver/wandb_internal":

func handleInformInit(nc *NexusConn, msg *service.ServerInformInitRequest) {
    log.Debug("PROCESS: INIT")

    // TODO make this a mapping
    log.Debug("STREAM init")
    // streamId := "thing"
    streamId := msg.XInfo.StreamId
    nc.mux[streamId] = &Stream{}
    nc.mux[streamId].init()

    // read from mux and write to nc
    go nc.mux[streamId].responder(nc)
}

func handleInformStart(nc *NexusConn, msg *service.ServerInformStartRequest) {
    log.Debug("PROCESS: START")
}

func handleInformFinish(nc *NexusConn, msg *service.ServerInformFinishRequest) {
    log.Debug("PROCESS: FIN")
}


func getStream(nc *NexusConn, streamId string) (*Stream) {
    //streamId := "thing"
    return nc.mux[streamId]
}

func handleInformRecord(nc *NexusConn, msg *service.Record) {
    streamId := msg.XInfo.StreamId
    stream := getStream(nc, streamId)

    ref := msg.ProtoReflect()
    desc := ref.Descriptor()
    num := ref.WhichOneof(desc.Oneofs().ByName("record_type")).Number()
    // fmt.Printf("PROCESS: COMM/PUBLISH %d\n", num)
    log.WithFields(log.Fields{"type": num}).Debug("PROCESS: COMM/PUBLISH")

    stream.handlerChan <-*msg
    // fmt.Printf("PROCESS: COMM/PUBLISH %d 2\n", num)
}

func handleInformTeardown(nc *NexusConn, msg *service.ServerInformTeardownRequest) {
    log.Debug("PROCESS: TEARDOWN")
    nc.done <-true
    // _, cancelCtx := context.WithCancel(nc.ctx)

    log.Debug("PROCESS: TEARDOWN *****1")
    //cancelCtx()
    log.Debug("PROCESS: TEARDOWN *****2")
    // TODO: remove this?
    //os.Exit(1)

    nc.server.shutdown = true
    nc.server.listen.Close()
}

func handleServerRequest(nc *NexusConn, msg service.ServerRequest) {
    switch x := msg.ServerRequestType.(type) {
    case *service.ServerRequest_InformInit:
        handleInformInit(nc, x.InformInit)
    case *service.ServerRequest_InformStart:
        handleInformStart(nc, x.InformStart)
    case *service.ServerRequest_InformFinish:
        handleInformFinish(nc, x.InformFinish)
    case *service.ServerRequest_RecordPublish:
        handleInformRecord(nc, x.RecordPublish)
    case *service.ServerRequest_RecordCommunicate:
        handleInformRecord(nc, x.RecordCommunicate)
    case *service.ServerRequest_InformTeardown:
        handleInformTeardown(nc, x.InformTeardown)
    case nil:
        // The field is not set.
        panic("bad2")
    default:
        bad := fmt.Sprintf("UNKNOWN type %T", x)
        panic(bad)
    }
}
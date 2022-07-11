let SerialTxBufferSize = 128
let SerialRxBufferSize = 64

serial.redirectToUSB()
serial.setWriteLinePadding(0)
serial.setTxBufferSize(SerialTxBufferSize)
serial.setRxBufferSize(SerialRxBufferSize)
let CmdNotifyReset = 0
let CmdComError = 255
let CmdComError_invalidStartByte = 1
send_numbers(CmdNotifyReset, [])

led.setDisplayMode(DisplayMode.BlackAndWhite)

let _send_numbers_packetNumber = 0
function send_numbers(cmd: number, numbers: number[]) {
    let timestamp = input.runningTimeMicros()
    let startByte = 0x80
    let bytesPerNumber = 4
    let headerLength = 8
    let checksumLength = 2
    let timestampPosition = 4
    let timestampLength = 4
    let length = Math.min(numbers.length, Math.floor((SerialTxBufferSize - headerLength - checksumLength) / bytesPerNumber))
    let bytesLength = timestampLength + length * bytesPerNumber + checksumLength
    let buffer = pins.createBuffer(headerLength + bytesLength)
    _send_numbers_packetNumber &= 0xFF
    buffer.setUint8(0, startByte)
    buffer.setUint8(1, cmd)
    buffer.setUint8(2, bytesLength)
    buffer.setUint8(3, _send_numbers_packetNumber)
    buffer.setNumber(NumberFormat.UInt32LE, timestampPosition, timestamp)
    let checksum = cmd + bytesLength + _send_numbers_packetNumber
    for (let j = 0; j != timestampLength; ++j) {
        checksum += buffer.getUint8(timestampPosition + j)
    }
    let bufferIndex = headerLength
    for (let i = 0; i != length; ++i) {
        buffer.setNumber(NumberFormat.Float32LE, bufferIndex, numbers[i])
        for (let j = 0; j != bytesPerNumber; ++j) {
            checksum += buffer.getUint8(bufferIndex + j)
        }
        bufferIndex += bytesPerNumber
    }
    buffer.setNumber(NumberFormat.UInt16LE, bufferIndex, checksum & 0xFFFF)
    serial.writeBuffer(buffer)
    _send_numbers_packetNumber += 1
}

//loops.everyInterval(500, function() {
input.onButtonPressed(Button.A, function () {
    send_numbers(0x01,[1234])
//                 [ input.acceleration(Dimension.X),
//                   input.acceleration(Dimension.Y),
//                   input.acceleration(Dimension.Z),
//                   input.acceleration(Dimension.Strength) ])
    led.toggle(2, 2)
})

"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
class Handler {
    constructor() {
        this.setNext = (next) => {
            this.next = next;
        };
        this.try = async (request) => {
            if (request.event === this.type) {
                await this.execute(request);
                return;
            }
            if (this.next) {
                this.next.try(request);
                return;
            }
            console.log(`ERROR: unknown event - ${request.event}`);
        };
    }
}
exports.default = Handler;
//# sourceMappingURL=Handler.js.map
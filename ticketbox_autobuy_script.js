class TicketBox {
    eventId = null;
    bookingId = null;
    order = null;
    recapchaKey = null;
    resultStep1 = {};
    resultStep2 = {};
    resultStep3 = {};
    email = null;
    phoneNumber = null;
    paymentType = 16; // MOMO
    quantityPerType = 1;
  
    intervalPyamentSuccess = null;
  
    constructor(url = '') {
      this.transformUrl(url);
      this.lookupRecaptchaKey();
      console.log("recapchaKey:", this.recapchaKey);
      this.initData();
    }
  
    static get variables() {
      const api = "https://ticketbox.vn/api";
  
      return {
        api,
        apiQrCode: 'https://api.qrserver.com/v1/create-qr-code/?data=&size=220x220', // replace data with momo link
      };
    }
  
    exec(quantity = 1) {
      this.quantityPerType = quantity;
      this.step1().then((data) => this.step2(data).then(data => this.step3(data).then(data => this.submitOrder(data).then())));
    }
  
    async start() {
      await this.step1();
    }
  
    async step1() {
      console.log("Start");
      console.time("Step1");
      // get ticket-booking information
      const url = `${TicketBox.variables.api}/event/${this.eventId}/ticket-booking/${this.bookingId}/event-info/false`;
  
      const data = await this.fetchData(url);
  
      console.log("Result step1", data);
  
      this.resultStep1 = data;
  
      console.timeEnd("Step1");
  
      return this.prepareDataStep2(data);
    }
  
    async step2(body) {
      console.time("Step2");
      // get ticket-booking information
      const url = `${TicketBox.variables.api}/event/${this.eventId}/ticket-booking/${this.bookingId}/submit-ticket-info`;
  
      if (!body.capcha) {
        body.capcha = await this.getCapcha();
      }
  
      const data = await this.postData(url, body);
  
      console.log("Result step2", data);
  
      this.resultStep2 = data.data;
  
      console.timeEnd("Step2");
  
      if (this.resultStep1.form) {
        return this.prepareDataStep3(data);
      }
  
    }
  
    async step3(body) {
      if (!this.resultStep1.form) {
  
        console.log("Bypass step3");
        return this.prepareDataStep4(this.bypassStep3());
      }
      console.time("Step3");
      // get ticket-booking information
      const url = `${TicketBox.variables.api}/event/${this.eventId}/ticket-booking/${this.bookingId}/submit-form-answers`;
  
      const data = await this.postData(url, body);
  
      console.log("Result step3", data);
  
      this.resultStep3 = data;
  
      console.timeEnd("Step3");
  
      return this.prepareDataStep4(data);
    }
  
    async submitOrder(body) {
      console.time("SubmitOrder");
      // get ticket-booking information
      const url = `${TicketBox.variables.api}/event/${this.eventId}/ticket-booking/${this.bookingId}/submit-order`;
  
      const data = await this.postData(url, body);
  
      console.log("Result SubmitOrder", data);
  
      console.timeEnd("SubmitOrder");
  
      return this.handleSuccess(data);
    }
  
    async handleSuccess(data) {
      if (data.data && data.data.redirectUrl) {
        console.log("Done order", data.data.finalAmount, data.data.redirectUrl);
        this.injectModalSuccess(data.data);
      } else {
        alert("Lỗi rồi, làm lại thôi, không có sao hết trơn á. Gõ lại runner.exec()")
      }
    }
  
    bypassStep3() {
      return {
        buyerInfo: this.resultStep2.buyerInfo,
        paymentInfo: {
          "deliveryInfo": {
            "note": null,
            "fee": 25000,
            "fullAddress": "2 Hải triều, Phường Bến Nghé, Quận 1, Thành Phố Hồ Chí Minh",
            "address": "2 Hải triều",
            "cityId": 79,
            "districtId": 760,
            "wardId": 3817
          },
          "officePickupInfo": {
            "note": null,
            "deadline": "2023-06-30T18:30:00+07:00"
          },
          "internetBankingInfo": null,
          "payooInfo": {
            "billingCode": null,
            "expireDate": "2023-07-01T21:51:49.7526195+07:00"
          },
          "one23Info": {
            "counter": {
              "counterCode": null
            },
            "expireDate": "2023-06-29T21:51:49.7526195+07:00",
            "encryptedData": null,
            "refNo1": null,
            "refNo2": null
          },
          "omiseInfo": {
            "omiseToken": null,
            "chargeToken": null
          },
          "bankTransferInfo": {
            "billingCode": null,
            "expireDate": "2023-06-29T21:51:49.7526195+07:00"
          },
          "cybersourceInfo": {
            "statusPayment": null,
            "returnMessage": null,
            "returnCode": null,
            "card": {
              "brand": null,
              "cardType": "",
              "expirationMonth": null,
              "expirationYear": null,
              "securityCode": null,
              "number": null,
              "maskedValidatedNumber": ""
            },
            "billingInfo": {
              "phone": null,
              "email": null,
              "address": null,
              "city": null,
              "country": null,
              "state": null,
              "zipCode": null
            }
          },
          "smartlinkInfo": {
            "statusPayment": null,
            "isSuccess": false,
            "isCancelled": true
          },
          "twoC2PInfo": {
            "statusPayment": null,
            "statusDescription": null,
            "isSuccess": false
          },
          "unipayAlipayInfo": {
            "statusPayment": null,
            "statusDescription": null,
            "paymentChannel": null,
            "isSuccess": false
          },
          "moMoInfo": {
            "statusDescription": ""
          }
        }
      }
    }
  
    prepareDataStep4(data) {
      const body = {
        buyerInfo: {
          ...data.buyerInfo,
          email: this.email,
          phoneNumber: this.phoneNumber,
        },
        officeId: 1,
        paymentInfo: {
          ...data.paymentInfo,
          paymentType: this.paymentType
        },
        receivingMethod: { receivingMethod: 1, noteDeliver: null }
      }
  
      return body;
    }
    prepareDataStep3(data) {
      const body = {
        commonFormAnswerSheet: null,
        formAnswerSheets: [],
        secretKey: "",
      };
  
      body.formAnswerSheets = this.resultStep2.orderDetails.map((d, index) => ({
        ...this.resultStep2.buyerInfo,
        phoneNumber: this.phoneNumber,
        email: this.email,
        formAnswers: this.resultStep1.form.ticketFormQuestions.map((tf) => ({
          formAnswerChoices: this.getFormAnswerChoices(tf),
          formAnswerSheetId: 0,
          formQuestionId: tf.id,
          id: 0,
          show: true,
        })),
        ticketType: this.resultStep1.currentShowing.ticketTypes[index],
        company: null,
        eventId: Number(this.eventId),
        isCommonForOrder: false,
        id: 0,
        jobTitle: null,
        open: false,
        ticketId: null,
        ticketTypeId: this.resultStep1.currentShowing.ticketTypes[index].id,
        valid: true,
        website: null,
      }));
  
      return body;
    }
    prepareDataStep2(data) {
      const body = {
        MobileOS: null,
        isWidget: false,
        orderDetails: [],
        capcha: window.capcha,
        secretKey: "",
        securityToken: window.securityToken,
      };
  
      body.orderDetails = data.currentShowing.ticketTypes
        .filter((t) => t.isAvailable && !t.isClosed)
        .map((ticketType) => ({
          ticketTypeId: ticketType.id,
          quantity: this.quantityPerType,
          sections: [],
        }));
  
      return body;
    }
  
  
    getFormAnswerChoices(tf) {
      const answerObj = {
        'Số điện thoại': this.phoneNumber,
        'Phone Number': this.phoneNumber,
        'SỐ ĐIỆN THOẠI CỦA BẠN': this.phoneNumber,
        'EMAIL CỦA BẠN': this.email,
        'Email': this.email,
      }
  
      const { formQuestionOptions, question = '', answerRequired, type } = tf;
  
      let answer = answerObj[question] ||  '';
      let formQuestionOptionId = null;
  
  
      switch (type) {
        case 3:
          if (Array.isArray(formQuestionOptions) && formQuestionOptions.length) {
            answer = formQuestionOptions[0].optionText || '';
            formQuestionOptionId = formQuestionOptions[0].id;
          }
          break;
        default:
          break;
      }
  
      if (answerRequired && !answer && type === 1) {
        if (question.toString().toLowerCase().includes('email')) {
          answer = this.email;
        } else {
          answer = this.phoneNumber;
        }
      } 
  
      
  
      return [
        {
          formAnswerChoiceComponents: [
            {
              answer,
              formAnswerChoiceId: 0,
              formQuestionOptionId,
              id: 0,
            }
          ],
          formAnswerId: 0,
          id: 0,
        }
      ]
    }
  
    transformUrl(url = '') {
      url = url || window.location.href;
      let regex = /\/event\/(\d+)\/ticket-booking\/(\d+)/;
  
      const match = url.match(regex);
      if (match) {
        const eventId = match[1];
        const bookingId = match[2];
        console.log("eventId:", eventId);
        console.log("bookingId:", bookingId);
  
        this.bookingId = bookingId;
        this.eventId = eventId;
      } else {
        throw new Error(
          "Please run in the page where the eventId and bookingId. Example: https://ticketbox.vn/event/may-lang-thang-liveshow-dan-truong-trung-quang-87284?opm=tbox.home.search.0"
        );
      }
    }
  
    async fetchData(url) {
      const response = await fetch(url);
      const jsonData = await response.json();
  
      return jsonData;
    }
  
    async postData(url = "", data = {}) {
      // Default options are marked with *
      const response = await fetch(url, {
        method: "POST", // *GET, POST, PUT, DELETE, etc.
        mode: "cors", // no-cors, *cors, same-origin
        cache: "no-cache", // *default, no-cache, reload, force-cache, only-if-cached
        credentials: "same-origin", // include, *same-origin, omit
        headers: {
          "Content-Type": "application/json",
          // 'Content-Type': 'application/x-www-form-urlencoded',
        },
        redirect: "follow", // manual, *follow, error
        referrerPolicy: "no-referrer", // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
        body: JSON.stringify(data), // body data type must match "Content-Type" header
      });
      return response.json(); // parses JSON response into native JavaScript objects
    }
  
    async getTokenReCaptCha() {
      return new Promise((resolve) => {
        grecaptcha.ready(() => {
          grecaptcha
            .execute(this.recapchaKey, { action: "booking" })
            .then(function (token) {
              resolve(token);
            })
            .catch((_) => resolve(""));
        });
      });
    }
  
    async getCapcha() {
      if (grecaptcha) {
        return this.getTokenReCaptCha();
      }
  
      return window.capcha || "";
    }
  
    lookupRecaptchaKey() {
      const total = document.scripts.length;
  
      const recaptchaSrc = "https://www.google.com/recaptcha/api.js?render=";
  
      for (let index = 0; index < total; index++) {
        const script = document.scripts.item(index);
  
        if (script.src.includes(recaptchaSrc)) {
          this.recapchaKey = script.src.split(recaptchaSrc)[1].split("&")[0];
          return;
        }
      }
    }
    initData() {
      const phone = this.getLocalStorage('phone');
      const email = this.getLocalStorage('email');
      this.phoneNumber = phone;
      this.email = email;
  
      if (!phone) {
        const phonePromt = prompt('Please enter a phone number');
  
        if (phonePromt) {
          this.setLocalStorage('phone', phonePromt);
          this.phoneNumber = phonePromt;
        }
      }
  
      if (!email) {
        const emailPromt = prompt('Please enter a email address');
  
        if (emailPromt) {
          this.setLocalStorage('email', emailPromt);
          this.email = emailPromt;
        }
      }
  
    }
  
    setLocalStorage(name, value) {
      localStorage.setItem(`HIHI_${name}`, value);
    }
  
    getLocalStorage(name) {
      return localStorage.getItem(`HIHI_${name}`);
    }
  
    formatPrice(price) {
      return new Intl.NumberFormat('en-US').format(price);
    }
  
    getCookie(cookie_name) {
      let c_name = cookie_name + "=";
      let cookie_decoded = decodeURIComponent(document.cookie);
      let cookie_parts = cookie_decoded.split(';');
      
      for(let i = 0; i <cookie_parts.length; i++) {
          let c = cookie_parts[i];
          while (c.charAt(0) == ' ') {
              c = c.substring(1);
          }
          if (c.indexOf(c_name) == 0) {
              return c.substring(c_name.length, c.length);
          }
      }
      return "";
    }
  
    subcribePaymentSuccess(data) {
      let url = "https://api-movie.ticketbox.vn/v2/payment/status?id=" + data.merchantTransactionID + "&method=momo";
  
      this.intervalPyamentSuccess = setInterval(() => {
  
        $.ajax({
          url,
          type: "GET",
          headers: {
              "x-tb-access-token": this.getCookie("TBoxJWT")
          },
          error: function(e) {
              console.log({
                  errorCallMomo: e
              })
          },
          success: (e) => {
            if (e && e.data && e.data.status && e.data.redirect_url) {
              const link = document.getElementById(`payment-success-momo-link-${data.merchantTransactionID}`);
  
              if (link) {
                const node = document.createElement('a');
                node.href = e.data.redirect_url;
                node.target = '_blank';
                node.html = 'Done';
                link.appendChild(node);
  
                node.click();
              }
              clearInterval(this.intervalPyamentSuccess);
            }
          }
        })
  
      }, 2000);
  
    }
  
    injectModalSuccess(data) {
  
      const { finalAmount, redirectUrl, merchantTransactionID } = data;
      const html = `
      <div id="modal-payment-momo" class="ng-scope">
        <div class="modal-backdrop">
          <div class="modal-content">
              <div class="modal-header">
                <div class="group-payment-method-name"><span><img class="payment-method-icon" src="https://static.tkbcdn.com/site/global/content/img/booking/momo.png"></span> <span class="payment-method-text ng-scope" translate="T.STEP2.MODAL_MOMO.TITLE_PAYMENT_METHOD">Thanh toán bằng ví MoMo</span></div>
              </div>
              <div class="modal-body">
                <div class="d-desk-flex">
                    <div class="group-img-qr-code">
                      <div class="img-qr-code"><img id="qrcode" width="220" src="https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(redirectUrl)}&amp;size=220x220"></div>
                      <div class="total"><span translate="T.STEP2.MODAL_MOMO.TOTAL" class="ng-scope">Tổng tiền</span> <span class="price"><span class="ng-binding">${this.formatPrice(finalAmount)}&nbsp;₫</span></span></div>
                    </div>
                    <div class="notes-payment-momo">
                      <div>
                          <div class="notes-title ng-scope" translate="T.STEP2.MODAL_MOMO.SCAN_QR">Quét mã QR để thanh toán</div>
                          <ul class="notes-list">
                            <li>
                                <div class="index-note">1</div>
                                <span><span translate="T.STEP2.MODAL_MOMO.NOTE_1.SUB_1" class="ng-scope">Mở</span>&nbsp; <span class="font-weight-600 ng-scope" translate="T.STEP2.MODAL_MOMO.NOTE_1.SUB_2">ứng dụng MoMo</span>&nbsp; <span translate="T.STEP2.MODAL_MOMO.NOTE_1.SUB_3" class="ng-scope">trên điện thoại</span></span>
                            </li>
                            <li>
                                <div class="index-note">2</div>
                                <div><span translate="T.STEP2.MODAL_MOMO.NOTE_2.SUB_1" class="ng-scope">Trên MoMo, chọn biểu tượng</span> <img src="https://static.tkbcdn.com/site/global/content/img/scan.png"> <span class="font-weight-600 ng-scope" translate="T.STEP2.MODAL_MOMO.NOTE_2.SUB_2">Quét mã QR</span></div>
                            </li>
                            <li>
                                <div class="index-note">3</div>
                                <span translate="T.STEP2.MODAL_MOMO.NOTE_3" class="ng-scope">Quét mã QR ở trang này và thanh toán</span>
                            </li>
                          </ul>
                      </div>
                      <div id="payment-success-momo-link-${merchantTransactionID}">
                      </div>
                    </div>
                </div>
              </div>
          </div>
        </div>
      </div>
      `;
  
      const modal = document.body.querySelector('#modal-payment-momo');
      if (modal) {
        modal.remove();
      }
  
      document.body.innerHTML += html;
  
      this.subcribePaymentSuccess(data);
  
    }
  }
  
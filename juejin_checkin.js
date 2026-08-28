/**
 * 稀土掘金每日签到 + 自动抽奖（Loon 版）
 * 基于原 juejin_checkin.py 的接口和业务流程转换
 *
 * 支持：
 * - 最多 5 个账号
 * - 每个账号：签到 -> 查询积分 -> 查询免费抽奖次数 -> 逐次抽奖
 * - Loon 通知执行结果
 *
 * 参数由插件 [Argument] 传入：
 * cookie1 / cookie2 / cookie3 / cookie4 / cookie5
 */

const BASE_URL = "https://api.juejin.cn";

const COMMON_HEADERS = {
  "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
  "Origin": "https://juejin.cn",
  "Referer": "https://juejin.cn/",
  "Accept": "application/json, text/plain, */*"
};

function getArg(name) {
  try {
    if ($argument && typeof $argument[name] !== "undefined" && $argument[name] !== null) {
      return String($argument[name]).trim();
    }
  } catch (_) {}
  return "";
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch (_) {
    return null;
  }
}

function request(method, url, cookie) {
  return new Promise((resolve) => {
    const params = {
      url,
      timeout: 15000,
      headers: {
        ...COMMON_HEADERS,
        "Cookie": cookie
      },
      "auto-redirect": true,
      "auto-cookie": true
    };

    const callback = (error, response, data) => {
      if (error) {
        resolve({
          ok: false,
          error: String(error),
          status: response && response.status,
          data: null
        });
        return;
      }

      const parsed = safeJson(data);
      resolve({
        ok: !!response && response.status >= 200 && response.status < 300,
        status: response ? response.status : 0,
        raw: data,
        data: parsed,
        error: null
      });
    };

    if (method === "POST") {
      $httpClient.post(params, callback);
    } else {
      $httpClient.get(params, callback);
    }
  });
}

async function checkIn(cookie) {
  const url = `${BASE_URL}/growth_api/v1/check_in?aid=5240`;
  const res = await request("POST", url, cookie);

  if (!res.ok) {
    return {
      success: false,
      already: false,
      message: `签到请求失败：${res.error || `HTTP ${res.status || "未知"}`}`
    };
  }

  if (!res.data) {
    return {
      success: false,
      already: false,
      message: "签到响应解析失败"
    };
  }

  const errNo = res.data.err_no;
  const errMsg = String(res.data.err_msg || "");

  if (errNo === 0) {
    return {
      success: true,
      already: false,
      message: "签到成功!"
    };
  }

  if (
    errNo === 403 ||
    errNo === 15001 ||
    errMsg.includes("今日已签到") ||
    errMsg.includes("请勿重复签到")
  ) {
    return {
      success: false,
      already: true,
      message: "今日已签到"
    };
  }

  return {
    success: false,
    already: false,
    message: `签到失败：${errMsg || "未知错误"} (错误码：${errNo})`
  };
}

async function getCurrentPoints(cookie) {
  const url = `${BASE_URL}/growth_api/v1/get_cur_point`;
  const res = await request("GET", url, cookie);

  if (!res.ok || !res.data) {
    return {
      success: false,
      points: 0,
      message: `获取积分失败：${res.error || `HTTP ${res.status || "未知"}`}`
    };
  }

  if (res.data.err_no === 0) {
    return {
      success: true,
      points: res.data.data ?? 0,
      message: ""
    };
  }

  return {
    success: false,
    points: 0,
    message: `获取积分失败：${res.data.err_msg || "未知错误"}`
  };
}

async function getLotteryConfig(cookie) {
  const url = `${BASE_URL}/growth_api/v1/lottery_config/get?aid=5240`;
  const res = await request("GET", url, cookie);

  if (!res.ok || !res.data) {
    return {
      success: false,
      freeCount: 0,
      message: `获取抽奖配置失败：${res.error || `HTTP ${res.status || "未知"}`}`
    };
  }

  if (res.data.err_no === 0) {
    const data = res.data.data || {};
    return {
      success: true,
      freeCount: Number(data.free_count || 0),
      message: ""
    };
  }

  return {
    success: false,
    freeCount: 0,
    message: res.data.err_msg || "获取抽奖配置失败"
  };
}

async function drawLottery(cookie) {
  const url = `${BASE_URL}/growth_api/v1/lottery/draw?aid=5240`;
  const res = await request("POST", url, cookie);

  if (!res.ok || !res.data) {
    return {
      success: false,
      message: `抽奖请求失败：${res.error || `HTTP ${res.status || "未知"}`}`
    };
  }

  if (res.data.err_no === 0) {
    const data = res.data.data || {};
    return {
      success: true,
      message: `抽奖结果：${data.lottery_name || "未中奖"}`
    };
  }

  return {
    success: false,
    message: `抽奖失败：${res.data.err_msg || "未知错误"}`
  };
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runAccount(name, cookie) {
  const result = {
    name,
    checkin: "",
    points: "",
    lottery: [],
  };

  console.log("==================================================");
  console.log(`[${name}] 稀土掘金签到开始`);
  console.log("==================================================");

  // 1. 签到
  const checkinResult = await checkIn(cookie);
  result.checkin = checkinResult.message;
  console.log(`[${name}] [1] ${checkinResult.message}`);

  // 2. 查询积分
  const pointsResult = await getCurrentPoints(cookie);
  if (pointsResult.success) {
    result.points = `当前积分：${pointsResult.points}`;
    console.log(`[${name}] [2] 当前积分：${pointsResult.points}`);
  } else {
    result.points = pointsResult.message;
    console.log(`[${name}] [2] ${pointsResult.message}`);
  }

  // 3. 抽奖
  const lotteryConfig = await getLotteryConfig(cookie);
  if (lotteryConfig.success) {
    console.log(`[${name}] [3] 剩余免费抽奖次数：${lotteryConfig.freeCount}`);

    if (lotteryConfig.freeCount > 0) {
      for (let i = 0; i < lotteryConfig.freeCount; i++) {
        const draw = await drawLottery(cookie);
        result.lottery.push(draw.message);
        console.log(`[${name}] [3.${i + 1}] ${draw.message}`);
        await sleep(1000);
      }
    } else {
      result.lottery.push("没有免费抽奖次数");
      console.log(`[${name}] [3] 没有免费抽奖次数`);
    }
  } else {
    result.lottery.push(lotteryConfig.message);
    console.log(`[${name}] [3] ${lotteryConfig.message}`);
  }

  console.log(`[${name}] 任务完成`);
  return result;
}

async function main() {
  const cookies = [
    ["账号1", getArg("cookie1")],
    ["账号2", getArg("cookie2")],
    ["账号3", getArg("cookie3")],
    ["账号4", getArg("cookie4")],
    ["账号5", getArg("cookie5")]
  ].filter(([, cookie]) => cookie);

  if (cookies.length === 0) {
    console.log("错误：没有配置任何掘金 Cookie。");
    $notification.post(
      "掘金自动签到",
      "执行失败",
      "没有配置 Cookie，请在 Loon 插件参数中填写。"
    );
    $done();
    return;
  }

  console.log(`共发现 ${cookies.length} 个账号，开始逐个执行...`);

  const results = [];

  for (const [name, cookie] of cookies) {
    try {
      const result = await runAccount(name, cookie);
      results.push(result);
    } catch (e) {
      const message = `执行异常：${e && e.message ? e.message : String(e)}`;
      console.log(`[${name}] ${message}`);
      results.push({
        name,
        checkin: message,
        points: "",
        lottery: []
      });
    }

    // 账号之间停 2 秒，保持和原 Python 脚本一致的节奏
    await sleep(2000);
  }

  const summaryLines = results.map(item => {
    const lottery = item.lottery && item.lottery.length
      ? `；${item.lottery.join("；")}`
      : "";
    return `${item.name}：${item.checkin}；${item.points || "积分查询失败"}${lottery}`;
  });

  const summary = summaryLines.join("\n");

  console.log("==================================================");
  console.log("全部账号处理完成！");
  console.log(summary);
  console.log("==================================================");

  $notification.post(
    "稀土掘金自动签到",
    `${cookies.length} 个账号执行完成`,
    summary
  );

  $done();
}

main().catch((e) => {
  console.log(`脚本异常：${e && e.stack ? e.stack : String(e)}`);
  $notification.post(
    "掘金自动签到",
    "脚本异常",
    e && e.message ? e.message : String(e)
  );
  $done();
});
